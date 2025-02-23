import time
import math
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

def set_preset4():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.MANUAL)
    device.registers.set_thermal_intensity(-1)
    device.registers.set_vibration_intensity(1)
    device.registers.set_vibration_frequency(200)
    status_label.config(text="Status: High Cooling & Strong Vibration")

# New presets without vibration
def set_preset5():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.OFF)
    device.registers.set_thermal_intensity(1.0)  # High heat
    device.registers.set_vibration_intensity(0.0)  # No vibration
    status_label.config(text="Status: High Heat & No Vibration")

def set_preset6():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.OFF)
    device.registers.set_thermal_intensity(-1.0)  # High cooling
    device.registers.set_vibration_intensity(0.0)  # No vibration
    status_label.config(text="Status: High Cooling & No Vibration")

def set_preset7():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.OFF)
    device.registers.set_thermal_intensity(0.3)  # Low heat
    device.registers.set_vibration_intensity(0.0)  # No vibration
    status_label.config(text="Status: Low Heat & No Vibration")

def set_preset8():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_vibration_mode(VibrationMode.OFF)
    device.registers.set_thermal_intensity(-0.3)  # Low cooling
    device.registers.set_vibration_intensity(0.0)  # No vibration
    status_label.config(text="Status: Low Cooling & No Vibration")

def stop():
    device.registers.set_thermal_mode(ThermalMode.OFF)
    device.registers.set_vibration_mode(VibrationMode.OFF)
    device.registers.set_vibration_intensity(0.0)
    device.registers.set_global_led(0, 0, 0)
    status_label.config(text="Status: Off")

def on_close():
    stop()  # Turn off the device when the window is closed
    tk_root.destroy()  # Close the Tkinter window

def get_skin_temperature():
    """
    Fetch the skin temperature from the device, truncate to the first decimal place, and update the temperature label.
    """
    temperature = device.get_skin_temperature()  # Assuming this is how you get the temperature
    truncated_temp = math.trunc(temperature * 10) / 10  # Truncate to 1 decimal place
    skin_temp_label.config(text=f"Skin Temperature: {truncated_temp} °C")
    tk_root.after(2000, get_skin_temperature)  # Update every 2000 ms (2 seconds)

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

# Create skin temperature label
skin_temp_label = tk.Label(tk_root, text="Skin Temperature: 0.0 °C", font=("Arial", 14), bg="black", fg="white")
skin_temp_label.pack(pady=10)

# Create buttons using grid system
button1 = create_button(frame, "Medium Heat & Vibration", set_preset1)
button2 = create_button(frame, "High Heat & Strong Vibration", set_preset2)
button3 = create_button(frame, "Light Cooling & Soft Vibration", set_preset3)
button4 = create_button(frame, "High Cooling & Strong Vibration", set_preset4)
button5 = create_button(frame, "High Heat & No Vibration", set_preset5)
button6 = create_button(frame, "High Cooling & No Vibration", set_preset6)
button7 = create_button(frame, "Low Heat & No Vibration", set_preset7)
button8 = create_button(frame, "Low Cooling & No Vibration", set_preset8)
button_stop = create_button(frame, "Stop", stop)

button1.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
button2.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
button3.grid(row=2, column=0, pady=10, padx=10, sticky="ew")
button4.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
button5.grid(row=4, column=0, pady=10, padx=10, sticky="ew")
button6.grid(row=5, column=0, pady=10, padx=10, sticky="ew")
button7.grid(row=6, column=0, pady=10, padx=10, sticky="ew")
button8.grid(row=7, column=0, pady=10, padx=10, sticky="ew")
button_stop.grid(row=8, column=0, pady=10, padx=10, sticky="ew")

# Adjust the grid weight for resizing
frame.grid_rowconfigure(0, weight=1)
frame.grid_rowconfigure(1, weight=1)
frame.grid_rowconfigure(2, weight=1)
frame.grid_rowconfigure(3, weight=1)
frame.grid_rowconfigure(4, weight=1)
frame.grid_rowconfigure(5, weight=1)
frame.grid_rowconfigure(6, weight=1)
frame.grid_rowconfigure(7, weight=1)
frame.grid_rowconfigure(8, weight=1)

# Bind the window close event to the on_close function
tk_root.protocol("WM_DELETE_WINDOW", on_close)

# Start getting the skin temperature
get_skin_temperature()

tk_root.mainloop()
