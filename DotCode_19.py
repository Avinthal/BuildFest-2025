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
    root.after(500, get_skin_temperature)

def calculate_thermal_intensity(device, target_temp):
    """Enhanced Proportional-Integral Control for accurate temperature regulation with adaptive damping."""
    global prev_error, integral_term

    if device not in prev_error:
        prev_error[device] = 0
        integral_term[device] = 0

    current_temp = device.registers.get_skin_temperature()
    error = target_temp - current_temp

    if abs(error) > 5:
        Kp = 0.3  
        Ki = 0.02  
    else:
        Kp = 0.15  
        Ki = 0.005  

    integral_term[device] += error
    integral_term[device] = max(min(integral_term[device], 10), -10)
    intensity = Kp * error + Ki * integral_term[device]
    intensity = max(-1.0, min(1.0, intensity))
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
    root.after(0, lambda: status_label.config(text=f"Status: Running {cycles} Cycles"))

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

def initialize_devices():
    """Discovers and initializes connected devices."""
    global devices
    devices = discover_devices(4)
    if not devices:
        print("No devices found! Check connections.")
        return False
    print(f"Connected devices: {len(devices)}")
    return True

if not initialize_devices():
    exit("No devices detected. Exiting.")

def run_carpal_tunnel_cycle():
    """Carpal Tunnel Cycle:
    - Max cold (-1.0) for 2.5 minutes with red LED.
    - Heating (target 40°C) for 10 minutes with red LED.
    """
    def phase_cold():
        root.after(0, lambda: status_label.config(text="Carpal Tunnel: Max Cold for 2.5 minutes"))
        for device in devices:
            try:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                device.registers.set_thermal_intensity(-1.0)
                device.registers.set_global_led(255, 0, 0)
                device.registers.set_vibration_mode(VibrationMode.OFF)
                device.registers.set_vibration_intensity(0.0)
            except Exception as e:
                print(f"Error in Carpal Tunnel Cold Phase: {e}")
        root.after(150000, phase_heat)  # 2.5 minutes
    
    def phase_heat():
        root.after(0, lambda: status_label.config(text="Carpal Tunnel: Heating at 40°C for 10 minutes"))
        for device in devices:
            try:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                intensity = calculate_thermal_intensity(device, 40)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_global_led(255, 0, 0)
                device.registers.set_vibration_mode(VibrationMode.OFF)
                device.registers.set_vibration_intensity(0.0)
            except Exception as e:
                print(f"Error in Carpal Tunnel Heat Phase: {e}")
        root.after(600000, stop)  # 10 minutes
    
    phase_cold()

def run_carpal_tunnel_demo_cycle():
    """Carpal Tunnel Demo Cycle:
    - Max cold for 10 seconds with red LED.
    - Heating (target 40°C) for 15 seconds with red LED.
    """
    root.after(0, lambda: status_label.config(text="Carpal Tunnel Demo: Max Cold for 10 seconds"))
    
    for device in devices:
        device.registers.set_thermal_mode(ThermalMode.MANUAL)
        device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
        device.registers.set_thermal_intensity(-1.0)
        device.registers.set_global_led(255, 0, 0)
        device.registers.set_vibration_mode(VibrationMode.OFF)
        device.registers.set_vibration_intensity(0.0)
    
    def transition_to_heating():
        root.after(0, lambda: status_label.config(text="Carpal Tunnel Demo: Heating at 40°C for 15 seconds"))
        for device in devices:
            device.registers.set_thermal_mode(ThermalMode.MANUAL)
            device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
            intensity = calculate_thermal_intensity(device, 40)
            device.registers.set_thermal_intensity(intensity)
            device.registers.set_global_led(255, 0, 0)
            device.registers.set_vibration_mode(VibrationMode.OFF)
            device.registers.set_vibration_intensity(0.0)
        root.after(15000, stop)
    
    root.after(10000, transition_to_heating)




def run_arthritis_cycle():
    """Arthritis Preset Cycle:
    - Phase 1: High heat (target 40°C) for 10 seconds with vibration at a valid intensity.
    - Phase 2: Max cold (thermal intensity -1.0) for 10 seconds with vibration at a valid intensity.
    - Phase 3: High heat (target 40°C) for 10 seconds with vibration at a valid intensity.
    """
    vibration_intensity = 1.0  # Ensure vibration intensity is within a valid range

    def phase_1():
        root.after(0, lambda: status_label.config(text="Arthritis: High Heat for 10 seconds"))
        for device in devices:
            try:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                intensity = calculate_thermal_intensity(device, 40)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(vibration_intensity)
                device.registers.set_global_led(255, 0, 0)
            except Exception as e:
                print(f"Error in Arthritis Phase 1: {e}")
        root.after(10000, phase_2)
    
    def phase_2():
        root.after(0, lambda: status_label.config(text="Arthritis: Max Cold for 15 seconds"))
        for device in devices:
            try:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                device.registers.set_thermal_intensity(-1.0)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(vibration_intensity)
                device.registers.set_global_led(255, 0, 0)
            except Exception as e:
                print(f"Error in Arthritis Phase 2: {e}")
        root.after(15000, phase_3)
    
    def phase_3():
        root.after(0, lambda: status_label.config(text="Arthritis: High Heat for 10 seconds"))
        for device in devices:
            try:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                intensity = calculate_thermal_intensity(device, 40)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(vibration_intensity)
                device.registers.set_global_led(255, 0, 0)
            except Exception as e:
                print(f"Error in Arthritis Phase 3: {e}")
        root.after(10000, stop)
    
    phase_1()

def run_mindfulness_demo_cycle():
    """Mindfulness Demo Cycle:
    - Lasts for 12 seconds, divided into 4 intervals of 3 seconds each.
    - In each interval, the LED alternates between green and blue.
    - At the start of each interval, a vibration beat is delivered.
    """
    intervals = [(0, 255, 0), (0, 0, 255), (0, 255, 0), (0, 0, 255)]
    
    def cycle_step(index):
        if index >= len(intervals):
            stop()
            return
        
        led_color = intervals[index]
        root.after(0, lambda: status_label.config(text=f"Mindfulness Demo: Interval {index + 1}"))
        
        for device in devices:
            try:
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                device.registers.set_global_led(*led_color)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(1.0)
            except Exception as e:
                print(f"Error in Mindfulness Interval {index + 1}: {e}")
        
        root.after(200, lambda: stop_vibration(index))
    
    def stop_vibration(index):
        for device in devices:
            try:
                device.registers.set_vibration_intensity(0.0)
            except Exception as e:
                print(f"Error stopping vibration in Mindfulness Interval {index + 1}: {e}")
        
        root.after(2800, lambda: cycle_step(index + 1))
    
    cycle_step(0)

def run_therapendant_mindfulness_demo_cycle():
    """Therapendant Mindfulness Demo Cycle:
    - Total duration: 8.5 seconds.
    - For the first 7 seconds: target temperature is set to 10°C with vibration at 26.63 Hz.
    - For the final 1.5 seconds: vibration increases to 53.26 Hz.
    - Throughout the cycle, the LED slowly alternates between blue and green (switching every 2 seconds).
    """
    led_colors = [(0, 0, 255), (0, 255, 0)]  # Blue and Green
    
    def cycle_step(elapsed):
        if stop_event.is_set() or elapsed >= 8.5:
            stop()
            return
        
        led_color = led_colors[int(elapsed // 2) % 2]
        vib_intensity = 26.63 if elapsed < 7 else 53.26
        
        root.after(0, lambda: status_label.config(text=f"Therapendant Mindfulness: {elapsed:.1f}s"))
        
        for device in devices:
            try:
                device.registers.set_global_led(*led_color)
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                intensity = calculate_thermal_intensity(device, 10)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(vib_intensity)
            except Exception as e:
                print(f"Error in Therapendant Mindfulness at {elapsed:.1f}s: {e}")
        
        root.after(100, lambda: cycle_step(elapsed + 0.1))
    
    cycle_step(0)



def start_carpal_tunnel_cycle():
    """Starts the Carpal Tunnel cycle in a separate thread."""
    global cycle_thread, stop_event
    if cycle_thread and cycle_thread.is_alive():
        return
    stop_event.clear()
    cycle_thread = threading.Thread(target=run_carpal_tunnel_cycle, daemon=True)
    cycle_thread.start()

def start_carpal_tunnel_demo_cycle():
    """Starts the Carpal Tunnel Demo cycle in a separate thread."""
    global cycle_thread, stop_event
    if cycle_thread and cycle_thread.is_alive():
        return
    stop_event.clear()
    cycle_thread = threading.Thread(target=run_carpal_tunnel_demo_cycle, daemon=True)
    cycle_thread.start()

def start_arthritis_cycle():
    """Starts the Arthritis preset cycle in a separate thread."""
    global cycle_thread, stop_event
    if cycle_thread and cycle_thread.is_alive():
        return
    stop_event.clear()
    cycle_thread = threading.Thread(target=run_arthritis_cycle, daemon=True)
    cycle_thread.start()

def start_mindfulness_demo_cycle():
    """Starts the Mindfulness Demo cycle in a separate thread."""
    global cycle_thread, stop_event
    if cycle_thread and cycle_thread.is_alive():
        return
    stop_event.clear()
    cycle_thread = threading.Thread(target=run_mindfulness_demo_cycle, daemon=True)
    cycle_thread.start()

def start_therapendant_mindfulness_demo_cycle():
    """Starts the Therapendant Mindfulness Demo cycle in a separate thread."""
    global cycle_thread, stop_event
    if cycle_thread and cycle_thread.is_alive():
        return
    stop_event.clear()
    cycle_thread = threading.Thread(target=run_therapendant_mindfulness_demo_cycle, daemon=True)
    cycle_thread.start()


def stop():
    """Stops the active cycle and resets devices."""
    stop_event.set()
    global cycle_thread
    if cycle_thread and cycle_thread.is_alive():
        cycle_thread.join(timeout=1)  # Ensure clean thread exit
    
    for device in devices:
        try:
            device.registers.set_thermal_mode(ThermalMode.OFF)
            device.registers.set_vibration_mode(VibrationMode.OFF)
            device.registers.set_thermal_intensity(0.0)
            device.registers.set_vibration_intensity(0.0)
            device.registers.set_global_led(0, 0, 0)  # Turn off LED
        except Exception as e:
            print(f"Error during stop: {e}")
    
    root.after(0, lambda: status_label.config(text="Status: Off"))

def on_close():
    stop()
    root.destroy()

def initialize_ui():
    """Creates the UI and initializes all widgets with a cream white background."""
    global root, status_label, skin_temp_label, preset_entry, preset_combobox
    global high_temp_entry, low_temp_entry, heat_duration_entry, cold_duration_entry, cycle_entry, vib_combobox

    root = tk.Tk()
    root.title("Thermal Device Controller")
    root.geometry("500x600")
    cream_bg = "#FFFDD0"
    root.configure(bg=cream_bg)

    status_label = tk.Label(root, text="Status: Idle", fg="black", bg=cream_bg, font=("Arial", 12))
    status_label.pack(pady=5)

    skin_temp_label = tk.Label(root, text="Skin Temperature: -- °C", fg="black", bg=cream_bg)
    skin_temp_label.pack(pady=5)
    get_skin_temperature()

    for label_text, var_name in [("Set High Temperature (°C):", "high_temp_entry"),
                                 ("Set Low Temperature (°C):", "low_temp_entry"),
                                 ("Heat Duration (seconds):", "heat_duration_entry"),
                                 ("Cold Duration (seconds):", "cold_duration_entry"),
                                 ("Number of Cycles:", "cycle_entry")]:
        tk.Label(root, text=label_text, fg="black", bg=cream_bg).pack()
        globals()[var_name] = tk.Entry(root, bg="white", fg="black")
        globals()[var_name].pack()

    vib_combobox = ttk.Combobox(root, values=["Off", "Low", "Medium", "High"], state="readonly")
    vib_combobox.pack(pady=5)
    vib_combobox.current(0)

    tk.Button(root, text="Apply Settings", command=apply_settings, bg=cream_bg, fg="black").pack(pady=5)
    tk.Button(root, text="Stop", command=stop, bg=cream_bg, fg="black").pack(pady=5)
    tk.Button(root, text="TheraBand Carpal Tunnel Preset", command=start_carpal_tunnel_cycle, bg=cream_bg, fg="black").pack(pady=5)
    tk.Button(root, text="TheraBand Carpal Tunnel Demo", command=start_carpal_tunnel_demo_cycle, bg=cream_bg, fg="black").pack(pady=5)
    tk.Button(root, text="TheraBand Arthritis Demo", command=start_arthritis_cycle, bg=cream_bg, fg="black").pack(pady=5)
    tk.Button(root, text="TheraBand Mindfulness Demo", command=start_mindfulness_demo_cycle, bg=cream_bg, fg="black").pack(pady=5)
    tk.Button(root, text="TheraPendant Mindfulness Demo", command=start_therapendant_mindfulness_demo_cycle, bg=cream_bg, fg="black").pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

devices = discover_devices(4)
initialize_ui()
