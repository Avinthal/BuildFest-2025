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
prev_error = {}       # Store previous error values for each device for better control
integral_term = {}    # Store integral error accumulation for each device

# UI Elements (to be initialized later)
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
    """Enhanced PI control for accurate temperature regulation with adaptive damping."""
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
                try:
                    device.registers.set_thermal_mode(ThermalMode.MANUAL)
                    device.registers.set_LED_mode(LedMode.GLOBAL_MANUAL)
                    intensity = calculate_thermal_intensity(device, high_temp)
                    device.registers.set_thermal_intensity(intensity)
                    device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
                    device.registers.set_vibration_intensity(vibration_intensity)
                except Exception as e:
                    print("Error during high temp phase:", e)
            time.sleep(heat_duration)
        if stop_event.is_set():
            break
        if low_temp is not None:
            for device in devices:
                try:
                    device.registers.set_thermal_mode(ThermalMode.MANUAL)
                    intensity = calculate_thermal_intensity(device, low_temp)
                    device.registers.set_thermal_intensity(intensity)
                    device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
                    device.registers.set_vibration_intensity(vibration_intensity)
                except Exception as e:
                    print("Error during low temp phase:", e)
            time.sleep(cold_duration)
    stop()

def run_carpal_tunnel_cycle():
    """
    Carpal Tunnel Cycle:
    - Max cold (-1.0) for 2.5 minutes with red LED.
    - Heating (target 40°C) for 10 minutes with red LED.
    """
    root.after(0, lambda: status_label.config(text="Carpal Tunnel: Max Cold for 2.5 minutes"))
    for device in devices:
        try:
            device.registers.set_thermal_mode(ThermalMode.MANUAL)
            device.registers.set_thermal_intensity(-1.0)
            device.registers.set_global_led(255, 0, 0)
            device.registers.set_vibration_mode(VibrationMode.OFF)
            device.registers.set_vibration_intensity(0.0)
        except Exception as e:
            print("Error in Carpal Tunnel (Cold Phase):", e)
    start_time = time.time()
    while time.time() - start_time < 150:
        if stop_event.is_set():
            stop()            
            return
        time.sleep(0.5)
    
    root.after(0, lambda: status_label.config(text="Carpal Tunnel: Heating at 40°C for 10 minutes"))
    start_time = time.time()
    while time.time() - start_time < 600:
        if stop_event.is_set():
            stop()
            return
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
                print("Error in Carpal Tunnel (Heating Phase):", e)
        time.sleep(1)
    stop()

def run_carpal_tunnel_demo_cycle():
    """
    Carpal Tunnel Demo Cycle:
    - Max cold for 10 seconds with red LED.
    - Heating (target 40°C) for 15 seconds with red LED.
    """
    root.after(0, lambda: status_label.config(text="Carpal Tunnel Demo: Max Cold for 10 seconds"))
    for device in devices:
        try:
            device.registers.set_thermal_mode(ThermalMode.MANUAL)
            device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
            device.registers.set_thermal_intensity(-1.0)
            device.registers.set_global_led(255, 0, 0)
            device.registers.set_vibration_mode(VibrationMode.OFF)
            device.registers.set_vibration_intensity(0.0)
        except Exception as e:
            print("Error in Carpal Tunnel Demo (Cold Phase):", e)
    start_time = time.time()
    while time.time() - start_time < 10:
        if stop_event.is_set():
            stop()
            return
        time.sleep(0.5)
    
    root.after(0, lambda: status_label.config(text="Carpal Tunnel Demo: Heating at 40°C for 15 seconds"))
    start_time = time.time()
    while time.time() - start_time < 15:
        if stop_event.is_set():
            stop()
            return
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
                print("Error in Carpal Tunnel Demo (Heating Phase):", e)
        time.sleep(1)
    stop()

def run_arthritis_cycle():
    """
    Arthritis Preset Cycle:
    - Phase 1: High heat (target 40°C) for 10 seconds with vibration at 15.66 Hz.
    - Phase 2: Max cold (thermal intensity -1.0) for 10 seconds with vibration at 15.66 Hz.
    - Phase 3: High heat (target 40°C) for 10 seconds with vibration at 15.66 Hz.
    In all phases, the LED is forced red.
    """
    # Phase 1: High Heat for 10 seconds
    root.after(0, lambda: status_label.config(text="Arthritis: High Heat for 10 seconds"))
    start_time = time.time()
    while time.time() - start_time < 10:
        if stop_event.is_set():
            stop()
            return
        for device in devices:
            try:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                intensity = calculate_thermal_intensity(device, 40)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(15.66)
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                device.registers.set_global_led(255, 0, 0)
            except Exception as e:
                print("Error in Arthritis Cycle Phase 1:", e)
        time.sleep(1)
    
    # Phase 2: Max Cold for 10 seconds
    root.after(0, lambda: status_label.config(text="Arthritis: Max Cold for 10 seconds"))
    start_time = time.time()
    while time.time() - start_time < 10:
        if stop_event.is_set():
            stop()
            return
        for device in devices:
            try:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                device.registers.set_thermal_intensity(-1.0)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(15.66)
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                device.registers.set_global_led(255, 0, 0)
            except Exception as e:
                print("Error in Arthritis Cycle Phase 2:", e)
        time.sleep(1)
    
    # Phase 3: High Heat for 10 seconds again
    root.after(0, lambda: status_label.config(text="Arthritis: High Heat for 10 seconds"))
    start_time = time.time()
    while time.time() - start_time < 10:
        if stop_event.is_set():
            stop()
            return
        for device in devices:
            try:
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                intensity = calculate_thermal_intensity(device, 40)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(15.66)
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                device.registers.set_global_led(255, 0, 0)
            except Exception as e:
                print("Error in Arthritis Cycle Phase 3:", e)
        time.sleep(1)
    stop()

def run_theraband_arthritis_cycle():
    """
    TheraBand Arthritis Preset:
    - Constant vibration at 15.66 Hz.
    - Phase 1: 2.5 minutes (150 sec) of max heat (thermal intensity 1.0).
    - Phase 2: 2.5 minutes of max cold (thermal intensity -1.0).
    - Phase 3: 2.5 minutes of max heat (thermal intensity 1.0).
    The LED is forced red in all phases.
    """
    phases = [
        ("Max Heat", 150, 1.0),
        ("Max Cold", 150, -1.0),
        ("Max Heat", 150, 1.0)
    ]
    for phase_name, duration, intensity_value in phases:
        root.after(0, lambda p=phase_name: status_label.config(text=f"TheraBand Arthritis: {p} Phase"))
        start_phase = time.time()
        while time.time() - start_phase < duration:
            if stop_event.is_set():
                stop()
                return
            for device in devices:
                try:
                    device.registers.set_thermal_mode(ThermalMode.MANUAL)
                    device.registers.set_thermal_intensity(intensity_value)
                    device.registers.set_vibration_mode(VibrationMode.MANUAL)
                    device.registers.set_vibration_intensity(15.66)
                    device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                    device.registers.set_global_led(255, 0, 0)
                except Exception as e:
                    print("Error in TheraBand Arthritis Cycle:", e)
            time.sleep(1)
    stop()

def run_mindfulness_demo_cycle():
    """
    Mindfulness Demo Cycle:
    - Lasts 12 seconds, divided into 4 intervals of 3 seconds.
    - In each interval, the LED alternates between green and blue.
    - At the start of each interval, a vibration beat is delivered.
    """
    total_duration = 12
    interval = 3
    num_intervals = total_duration // interval
    for i in range(num_intervals):
        led_color = (0, 255, 0) if i % 2 == 0 else (0, 0, 255)
        root.after(0, lambda idx=i: status_label.config(text=f"Mindfulness Demo: Interval {idx+1}"))
        for device in devices:
            try:
                device.registers.set_global_led(*led_color)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                device.registers.set_vibration_intensity(1.0)
            except Exception as e:
                print("Error in Mindfulness Demo (beat):", e)
        time.sleep(0.2)
        for device in devices:
            try:
                device.registers.set_vibration_intensity(0.0)
            except Exception as e:
                print("Error turning off vibration:", e)
        start_interval = time.time()
        while time.time() - start_interval < (interval - 0.2):
            if stop_event.is_set():
                stop()
                return
            time.sleep(0.1)
    stop()

def run_therapendant_mindfulness_demo_cycle():
    """
    Therapendant Mindfulness Demo Cycle:
    - Total 8.5 seconds.
    - First 7 sec: target temperature 10°C with vibration at 26.63 Hz.
    - Final 1.5 sec: vibration increases to 53.26 Hz.
    - LED slowly alternates between blue and green (switching every 2 sec).
    """
    start_time = time.time()
    total_duration = 8.5
    while time.time() - start_time < total_duration:
        elapsed = time.time() - start_time
        led_color = (0, 0, 255) if int(elapsed // 2) % 2 == 0 else (0, 255, 0)
        for device in devices:
            try:
                device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
                device.registers.set_global_led(*led_color)
                device.registers.set_thermal_mode(ThermalMode.MANUAL)
                intensity = calculate_thermal_intensity(device, 0)
                device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL)
                vib_intensity = .2 if elapsed < 7 else .9
                device.registers.set_vibration_intensity(vib_intensity)
            except Exception as e:
                print("Error in Therapendant Mindfulness Demo:", e)
        time.sleep(0.1)
    stop()

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

def start_theraband_arthritis_cycle():
    """Starts the TheraBand Arthritis Preset cycle in a separate thread."""
    global cycle_thread, stop_event
    if cycle_thread and cycle_thread.is_alive():
        return
    stop_event.clear()
    cycle_thread = threading.Thread(target=run_theraband_arthritis_cycle, daemon=True)
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
    """Stops the active process and resets devices."""
    stop_event.set()
    for device in devices:
        try:
            device.registers.set_thermal_mode(ThermalMode.OFF)
            device.registers.set_vibration_mode(VibrationMode.OFF)
            device.registers.set_thermal_intensity(0.0)
            device.registers.set_vibration_intensity(0.0)
            device.registers.set_global_led(0, 0, 0)  # Reset LED to off
        except Exception as e:
            print(f"Error during stop: {e}")
    print("Cycle stopped.")

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