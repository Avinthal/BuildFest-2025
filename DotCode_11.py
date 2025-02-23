import time
import math
import tkinter as tk
from tkinter import ttk, Canvas
from datafeel.device import ThermalMode, LedMode, VibrationMode, discover_devices

ascii_watch = """
       .--------.
      /          \ 
     |  | 12  |  |
     |  |  o   |  |
     |  | 9  3 |  |
     |  |  6   |  |
     |   '----'  |
      \________/
"""

presets = {}

def save_preset():
    name = preset_entry.get()
    if name:
        presets[name] = {
            "high_temperature": high_temp_entry.get(),
            "low_temperature": low_temp_entry.get(),
            "vibration": vib_combobox.get(),
            "heat_duration": heat_duration_entry.get(),
            "cold_duration": cold_duration_entry.get(),
            "cycles": cycle_entry.get()
        }
        preset_combobox['values'] = list(presets.keys())

def load_preset():
    name = preset_combobox.get()
    if name in presets:
        high_temp_entry.delete(0, tk.END)
        high_temp_entry.insert(0, presets[name]["high_temperature"])
        low_temp_entry.delete(0, tk.END)
        low_temp_entry.insert(0, presets[name]["low_temperature"])
        vib_combobox.set(presets[name]["vibration"])
        heat_duration_entry.delete(0, tk.END)
        heat_duration_entry.insert(0, presets[name]["heat_duration"])
        cold_duration_entry.delete(0, tk.END)
        cold_duration_entry.insert(0, presets[name]["cold_duration"])
        cycle_entry.delete(0, tk.END)
        cycle_entry.insert(0, presets[name]["cycles"])

def apply_settings():
    try:
        high_temp = high_temp_entry.get()
        low_temp = low_temp_entry.get()
        high_temp = float(high_temp) if high_temp else None
        low_temp = float(low_temp) if low_temp else None
        cycles = int(cycle_entry.get())
        heat_duration = int(heat_duration_entry.get())
        cold_duration = int(cold_duration_entry.get())
        vibration_intensity = vib_combobox.get()
    except ValueError:
        status_label.config(text="Invalid Input")
        return
    
    if not high_temp and not low_temp:
        status_label.config(text="At least one temperature must be set")
        return
    
    vibration_values = {
        "Off": 0.0,
        "Low": 0.3,
        "Medium": 0.5,
        "High": 1.0
    }
    vibration_intensity = vibration_values.get(vibration_intensity, 0.0)
    
    for device in devices:
        device.registers.set_thermal_mode(ThermalMode.MANUAL)
        device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
        device.registers.set_vibration_intensity(vibration_intensity)
        device.registers.set_vibration_frequency(150 if vibration_intensity > 0 else 0)
    
    def cycle_heat_cold(cycle_count):
        if cycle_count == 0:
            return
        for device in devices:
            if high_temp is not None:
                device.registers.set_thermal_intensity(1.0)
        root.after(heat_duration * 1000, lambda: cycle_cold(cycle_count - 1))
    
    def cycle_cold(cycle_count):
        if cycle_count == 0:
            return
        for device in devices:
            if low_temp is not None:
                device.registers.set_thermal_intensity(-1.0)
        root.after(cold_duration * 1000, lambda: cycle_heat_cold(cycle_count - 1))
    
    cycle_heat_cold(cycles)
    status_label.config(text=f"Status: Running {cycles} Cycles, Heat {heat_duration}s, Cold {cold_duration}s")

def stop():
    for device in devices:
        device.registers.set_thermal_mode(ThermalMode.OFF)
        device.registers.set_vibration_mode(VibrationMode.OFF)
        device.registers.set_global_led(255, 0, 0)
    status_label.config(text="Status: Off")

def on_close():
    stop()
    root.destroy()

devices = discover_devices(2)
if not devices:
    exit()

for device in devices:
    device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
    device.registers.set_global_led(255, 0, 0)

root = tk.Tk()
root.title("Thermal Device Controller")
root.geometry("500x600")
root.configure(bg="black")

ascii_watch_label = tk.Label(root, text=ascii_watch, fg="white", bg="black", font=("Courier", 8))
ascii_watch_label.pack()

status_label = tk.Label(root, text="Status: Idle", fg="white", bg="black", font=("Arial", 12))
status_label.pack(pady=5)

high_temp_label = tk.Label(root, text="Set High Temperature (°C):", fg="white", bg="black")
high_temp_label.pack()
high_temp_entry = tk.Entry(root)
high_temp_entry.pack()

low_temp_label = tk.Label(root, text="Set Low Temperature (°C):", fg="white", bg="black")
low_temp_label.pack()
low_temp_entry = tk.Entry(root)
low_temp_entry.pack()

vib_label = tk.Label(root, text="Vibration Strength:", fg="white", bg="black")
vib_label.pack()
vib_combobox = ttk.Combobox(root, values=["Off", "Low", "Medium", "High"], state="readonly")
vib_combobox.pack(pady=5)
vib_combobox.current(0)

heat_duration_label = tk.Label(root, text="Heat Duration (seconds):", fg="white", bg="black")
heat_duration_label.pack()
heat_duration_entry = tk.Entry(root)
heat_duration_entry.pack()

cold_duration_label = tk.Label(root, text="Cold Duration (seconds):", fg="white", bg="black")
cold_duration_label.pack()
cold_duration_entry = tk.Entry(root)
cold_duration_entry.pack()

cycle_label = tk.Label(root, text="Number of Cycles:", fg="white", bg="black")
cycle_label.pack()
cycle_entry = tk.Entry(root)
cycle_entry.pack()

apply_button = tk.Button(root, text="Apply Settings", command=apply_settings)
apply_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop", command=stop)
stop_button.pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
