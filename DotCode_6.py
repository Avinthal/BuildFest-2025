import time
import math
import tkinter as tk
from tkinter import ttk, colorchooser
from datafeel.device import ThermalMode, LedMode, VibrationMode, discover_devices

def apply_settings():
    thermal_values = {
        "Very Low": -1.0,
        "Low": -0.5,
        "Medium": 0.0,
        "High": 0.5,
        "Very High": 1.0
    }
    vibration_values = {
        "Off": 0.0,
        "Low": 0.3,
        "Medium": 0.5,
        "High": 1.0
    }
    
    
    thermal_intensity = thermal_values[temp_combobox.get()]
    vibration_intensity = vibration_values[vib_combobox.get()]
    
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
    device.registers.set_thermal_intensity(thermal_intensity)
    device.registers.set_vibration_intensity(vibration_intensity)
    device.registers.set_vibration_frequency(150 if vibration_intensity > 0 else 0)
    status_label.config(text=f"Status: {temp_combobox.get()} Temperature & {vib_combobox.get()} Vibration")
    duration = int(timer_entry.get())
    root.after(duration * 1000, stop)
    
    

def set_timer():
    try:
        duration = int(timer_entry.get())
        root.after(duration * 1000, stop)
    except ValueError:
        pass

def choose_color():
    color_code = colorchooser.askcolor(title="Choose LED Color")[0]
    if color_code:
        r, g, b = map(int, color_code)
        device.registers.set_global_led(r, g, b)

def get_skin_temperature():
    temperature = device.get_skin_temperature()
    truncated_temp = math.trunc(temperature * 10) / 10
    skin_temp_label.config(text=f"Skin Temperature: {truncated_temp} °C")
    root.after(2000, get_skin_temperature)

def stop():
    device.registers.set_thermal_mode(ThermalMode.OFF)
    device.registers.set_vibration_mode(VibrationMode.OFF)
    device.registers.set_global_led(0, 0, 0)
    status_label.config(text="Status: Off")

def on_close():
    stop()
    root.destroy()

devices = discover_devices(1)
if not devices:
    exit()

device = devices[0]
device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
device.registers.set_global_led(255, 0, 0)

root = tk.Tk()
root.title("Thermal Device Controller")
root.geometry("400x600")
root.configure(bg="black")

status_label = tk.Label(root, text="Status: Idle", fg="white", bg="black", font=("Arial", 12))
status_label.pack(pady=5)

temp_combobox = ttk.Combobox(root, values=["Very Low", "Low", "Medium", "High", "Very High"], state="readonly")
temp_combobox.pack(pady=5)
temp_combobox.current(2)

vib_combobox = ttk.Combobox(root, values=["Off", "Low", "Medium", "High"], state="readonly")
vib_combobox.pack(pady=5)
vib_combobox.current(0)

apply_button = tk.Button(root, text="Apply Settings", command=apply_settings)
apply_button.pack(pady=5)

timer_label = tk.Label(root, text="Set Timer (seconds):", fg="white", bg="black")
timer_label.pack()
timer_entry = tk.Entry(root)
timer_entry.pack()


color_button = tk.Button(root, text="Choose LED Color", command=choose_color)
color_button.pack(pady=5)

skin_temp_label = tk.Label(root, text="Skin Temperature: 0.0 °C", fg="white", bg="black")
skin_temp_label.pack(pady=5)

stop_button = tk.Button(root, text="Stop", command=stop)
stop_button.pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_close)
get_skin_temperature()
root.mainloop()