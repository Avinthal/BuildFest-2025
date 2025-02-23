import time
import tkinter as tk
from datafeel.device import ThermalMode, LedMode, VibrationMode, discover_devices

def set_preset1():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.MANUAL)
    device.registers.set_thermal_intensity(0.5)
    device.registers.set_vibration_intensity(0.5)
    device.registers.set_vibration_frequency(150)
    status_label.config(text="Status: Medium Heat & Vibration")

def set_preset2():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.MANUAL)
    device.registers.set_thermal_intensity(1.0)
    device.registers.set_vibration_intensity(1.0)
    device.registers.set_vibration_frequency(200)
    status_label.config(text="Status: High Heat & Strong Vibration")

def set_preset3():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.MANUAL)
    device.registers.set_thermal_intensity(-0.5)
    device.registers.set_vibration_intensity(0.3)
    device.registers.set_vibration_frequency(100)
    status_label.config(text="Status: Light Cooling & Soft Vibration")

def stop():
    device.registers.set_thermal_mode(ThermalMode.OFF)
    device.registers.set_vibration_intensity(0.0)
    device.registers.set_global_led(0, 0, 0)
    status_label.config(text="Status: Off")

devices = discover_devices(1)  
if not devices:
    print("No devices found.")
    exit()

device = devices[0]
print("Device found:", device)

device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
device.registers.set_global_led(255, 0, 0)

tk_root = tk.Tk()
tk_root.title("Thermal Control")
tk_root.configure(bg="black")

# Create buttons in grid layout
def create_button(frame, text, command):
    button = tk.Button(frame, text=text, font=("Arial", 12, "bold"), command=command, width=20, height=2, relief="solid", bg="#F5F5DC")
    return button

frame = tk.Frame(tk_root, bg="black")
frame.pack(fill=tk.BOTH, expand=True)

# Create status label
status_label = tk.Label(tk_root, text="Status: Idle", font=("Arial", 14), bg="black", fg="white")
status_label.pack(pady=10)

# Create buttons using grid system
button1 = create_button(frame, "Medium Heat & Vibration", set_preset1)
button2 = create_button(frame, "High Heat & Strong Vibration", set_preset2)
button3 = create_button(frame, "Light Cooling & Soft Vibration", set_preset3)
button_stop = create_button(frame, "Stop", stop)

button1.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
button2.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
button3.grid(row=2, column=0, pady=10, padx=10, sticky="ew")
button_stop.grid(row=3, column=0, pady=10, padx=10, sticky="ew")

# Adjust the grid weight for resizing
frame.grid_rowconfigure(0, weight=1)
frame.grid_rowconfigure(1, weight=1)
frame.grid_rowconfigure(2, weight=1)
frame.grid_rowconfigure(3, weight=1)

tk_root.mainloop()

