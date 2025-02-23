import time
import math
import tkinter as tk
from tkinter import ttk, colorchooser, Canvas
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

def apply_settings():
    try:
        target_temperature = float(temp_entry.get())
    except ValueError:
        status_label.config(text="Invalid Temperature Input")
        return
    
    vibration_values = {
        "Off": 0.0,
        "Low": 0.3,
        "Medium": 0.5,
        "High": 1.0
    }
    
    vibration_intensity = vibration_values.get(vib_combobox.get(), 0.0)
    
    for device in devices:
        device.registers.set_thermal_mode(ThermalMode.MANUAL)
        device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
        device.registers.set_thermal_intensity(0.0)  # Start at neutral intensity
        device.registers.set_vibration_intensity(vibration_intensity)
        device.registers.set_vibration_frequency(150 if vibration_intensity > 0 else 0)
    
    status_label.config(text=f"Temperature Status: Target Temp {target_temperature}°C \n Vibration Status: {vib_combobox.get()}")
    
    def feedback_loop():
        for device in devices:
            current_temp = device.get_skin_temperature()
            error = target_temperature - current_temp
            
            # Adjust intensity within the valid range
            intensity = max(-1.0, min(1.0, error * 0.1))  # Proportional adjustment
            device.registers.set_thermal_intensity(intensity)
            skin_temp_label.config(text=f"Skin Temperature: {round(current_temp, 1)}°C")

        if abs(error) > 0.5:  # Continue adjusting if the error is significant
            root.after(2000, feedback_loop)
    
    feedback_loop()

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
        for device in devices:
            device.registers.set_global_led(r, g, b)

def get_skin_temperature():
    for device in devices:
        temperature = device.get_skin_temperature()
        skin_temp_label.config(text=f"Skin Temperature: {temperature} °C")
    root.after(2000, get_skin_temperature)

def stop():
    for device in devices:
        device.registers.set_thermal_mode(ThermalMode.OFF)
        device.registers.set_vibration_mode(VibrationMode.OFF)
        device.registers.set_global_led(0, 0, 0)
    status_label.config(text="Status: Off")

def on_close():
    stop()
    root.destroy()

devices = discover_devices(3)
if not devices:
    exit()

for device in devices:
    device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
    device.registers.set_global_led(255, 0, 0)

root = tk.Tk()
root.title("Thermal Device Controller")
root.geometry("400x600")
root.configure(bg="black")

ascii_watch_label = tk.Label(root, text=ascii_watch, fg="white", bg="black", font=("Alata", 8))
ascii_watch_label.pack()

status_label = tk.Label(root, text="Status: Idle", fg="white", bg="black", font=("Alata", 12))
status_label.pack(pady=5)

temp_label = tk.Label(root, text="Set Target Temperature (°C):", fg="white", bg="black")
temp_label.pack()
temp_entry = tk.Entry(root)
temp_entry.pack()

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
