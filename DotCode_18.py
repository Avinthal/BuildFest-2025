import time
import threading
import tkinter as tk
from tkinter import ttk
from datafeel.device import ThermalMode, LedMode, VibrationMode, discover_devices

# Global Variables
presets = {}
stop_event = threading.Event()
cycle_thread = None
devices = []
prev_error = {}  # Store previous error values for each device for better control
integral_term = {}  # Store integral error accumulation for each device

# UI Elements (To be initialized later)
root = None
status_label = None
skin_temp_label = None
preset_entry = None
preset_combobox = None
high_temp_entry = None
low_temp_entry = None
heat_duration_entry = None
cold_duration_entry = None
cycle_entry = None
vib_combobox = None

def get_skin_temperature():
    """Continuously updates the skin temperature reading every 0.5 seconds for real-time accuracy."""
    for device in devices:
        try:
            temperature = device.registers.get_skin_temperature()
            skin_temp_label.config(text=f"Skin Temperature: {temperature:.1f} °C")
        except Exception as e:
            skin_temp_label.config(text="Error reading temperature")
    root.after(500, get_skin_temperature)  # Update every 0.5 seconds

def calculate_thermal_intensity(device, target_temp):
    """Enhanced Proportional-Integral Control for accurate temperature regulation with adaptive damping."""
    global prev_error, integral_term

    if device not in prev_error:
        prev_error[device] = 0
        integral_term[device] = 0

    current_temp = device.registers.get_skin_temperature()
    error = target_temp - current_temp

    # Adjust the control response dynamically
    if abs(error) > 5:  # If error is large, react more aggressively
        Kp = 0.3  
        Ki = 0.02  
    else:  # If close to the target, make small refinements
        Kp = 0.15  
        Ki = 0.005  

    integral_term[device] += error
    integral_term[device] = max(min(integral_term[device], 10), -10)  # Prevent excessive accumulation

    intensity = Kp * error + Ki * integral_term[device]
    intensity = max(-1.0, min(1.0, intensity))  # Clamp between -1.0 and 1.0

    prev_error[device] = error

    return intensity

def apply_settings():
    """Applies user-selected settings and starts the cycle process in a separate thread."""
    global cycle_thread, stop_event

    if cycle_thread and cycle_thread.is_alive():
        return  

    try:
        high_temp = float(high_temp_entry.get().strip()) if high_temp_entry.get().strip() else None
        low_temp = float(low_temp_entry.get().strip()) if low_temp_entry.get().strip() else None
        cycles = int(cycle_entry.get().strip())
        heat_duration = int(heat_duration_entry.get().strip())
        cold_duration = int(cold_duration_entry.get().strip())
        vibration_intensity = vib_combobox.get()
    except ValueError:
        status_label.config(text="Invalid Input: Enter numbers only.")
        return

    if high_temp is None and low_temp is None:
        status_label.config(text="At least one temperature must be set.")
        return

    vibration_values = {"Off": 0.0, "Low": 0.3, "Medium": 0.5, "High": 1.0}
    vibration_intensity = vibration_values.get(vibration_intensity, 0.0)

    stop_event.clear()

    cycle_thread = threading.Thread(target=run_cycles, args=(cycles, high_temp, low_temp, heat_duration, cold_duration, vibration_intensity), daemon=True)
    cycle_thread.start()

def run_cycles(cycles, high_temp, low_temp, heat_duration, cold_duration, vibration_intensity):
    """Handles the heating and cooling cycles in a controlled loop."""
    status_label.config(text=f"Status: Running {cycles} Cycles")

    for i in range(cycles):
        if stop_event.is_set():
            break  

        if high_temp is not None:
            for device in devices:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                intensity = calculate_thermal_intensity(device, high_temp)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
                device.registers.set_vibration_intensity(vibration_intensity)
            time.sleep(heat_duration)

        if stop_event.is_set():
            break

        if low_temp is not None:
            for device in devices:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                intensity = calculate_thermal_intensity(device, low_temp)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
                device.registers.set_vibration_intensity(vibration_intensity)
            time.sleep(cold_duration)

    stop()

def stop():
    """Stops the active process and resets devices."""
    global stop_event
    stop_event.set()  

    for device in devices:
        device.registers.set_thermal_mode(ThermalMode.OFF)
        device.registers.set_vibration_mode(VibrationMode.OFF)
        device.registers.set_thermal_intensity(0.0)
        device.registers.set_vibration_intensity(0.0)
        device.registers.set_global_led(255, 0, 0)

    status_label.config(text="Status: Off")

def on_close():
    stop()
    root.destroy()

def initialize_ui():
    """Creates the UI and initializes all widgets."""
    global root, status_label, skin_temp_label, preset_entry, preset_combobox
    global high_temp_entry, low_temp_entry, heat_duration_entry, cold_duration_entry, cycle_entry, vib_combobox

    root = tk.Tk()
    root.title("Thermal Device Controller")
    root.geometry("500x600")
    root.configure(bg="black")

    status_label = tk.Label(root, text="Status: Idle", fg="white", bg="black", font=("Arial", 12))
    status_label.pack(pady=5)

    skin_temp_label = tk.Label(root, text="Skin Temperature: -- °C", fg="white", bg="black")
    skin_temp_label.pack(pady=5)
    get_skin_temperature()

    for label, var_name in [("Set High Temperature (°C):", "high_temp_entry"),
                            ("Set Low Temperature (°C):", "low_temp_entry"),
                            ("Heat Duration (seconds):", "heat_duration_entry"),
                            ("Cold Duration (seconds):", "cold_duration_entry"),
                            ("Number of Cycles:", "cycle_entry")]:
        tk.Label(root, text=label, fg="white", bg="black").pack()
        globals()[var_name] = tk.Entry(root)
        globals()[var_name].pack()

    vib_combobox = ttk.Combobox(root, values=["Off", "Low", "Medium", "High"], state="readonly")
    vib_combobox.pack(pady=5)
    vib_combobox.current(0)

    tk.Button(root, text="Apply Settings", command=apply_settings).pack(pady=5)
    tk.Button(root, text="Stop", command=stop).pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

devices = discover_devices(3)
initialize_ui()
