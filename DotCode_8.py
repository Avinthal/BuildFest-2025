import time
import math
import tkinter as tk
from tkinter import ttk, colorchooser
from datafeel.device import ThermalMode, LedMode, VibrationMode, discover_devices

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
    
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
    device.registers.set_thermal_intensity(0.0)  # Start at neutral intensity
    device.registers.set_vibration_intensity(vibration_intensity)
    device.registers.set_vibration_frequency(150 if vibration_intensity > 0 else 0)
    status_label.config(text=f"Status: Target Temp {target_temperature}°C & {vib_combobox.get()} Vibration")
    
    def feedback_loop():
        current_temp = device.get_skin_temperature()
        error = target_temperature - current_temp
        
        # Adjust intensity within the valid range
        intensity = max(-1.0, min(1.0, error * 0.1))  # Proportional adjustment
        device.registers.set_thermal_intensity(intensity)
        skin_temp_label.config(text=f"Skin Temperature: {round(current_temp, 1)}°C")
        temp_bar['value'] = max(0, min(100, (current_temp + 10) * 5))  # Normalize to range 0-100

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
        device.registers.set_global_led(r, g, b)

def get_skin_temperature():
    temperature = device.get_skin_temperature()
    truncated_temp = math.trunc(temperature * 10) / 10
    skin_temp_label.config(text=f"Skin Temperature: {truncated_temp} °C")
    temp_bar['value'] = max(0, min(100, (temperature + 10) * 5))  # Normalize to range 0-100
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

status_label = tk.Label(root, text="Status: Idle", fg="white", bg="black", font=("Alata", 12))
status_label.pack(pady=5)

temp_label = tk.Label(root, text="Set Target Temperature (°C):", fg="white", bg="black", font=("Alata", 12))
temp_label.pack()
temp_entry = tk.Entry(root)
temp_entry.pack()

vib_combobox = ttk.Combobox(root, values=["Off", "Low", "Medium", "High"], state="readonly", font=("Alata", 12))
vib_combobox.pack(pady=5)
vib_combobox.current(0)

apply_button = tk.Button(root, text="Apply Settings", command=apply_settings)
apply_button.pack(pady=5)

timer_label = tk.Label(root, text="Set Timer (seconds):", fg="white", bg="black", font=("Alata", 12))
timer_label.pack()
timer_entry = tk.Entry(root)
timer_entry.pack()

color_button = tk.Button(root, text="Choose LED Color", command=choose_color)
color_button.pack(pady=5)

skin_temp_label = tk.Label(root, text="Skin Temperature: 0.0 °C", fg="white", bg="black")
skin_temp_label.pack(pady=5)

temp_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
temp_bar.pack(pady=5)

stop_button = tk.Button(root, text="Stop", command=stop)
stop_button.pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_close)
get_skin_temperature()
root.mainloop()
