import time
import tkinter as tk
from datafeel.device import ThermalMode, LedMode, VibrationMode, discover_devices

def set_preset1():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_thermal_intensity(0.5)
    device.registers.set_vibration_intensity(0.5)
    device.registers.set_vibration_frequency(150)
    status_label.config(text="Status: Medium Heat & Vibration")

def set_preset2():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_thermal_intensity(1.0)
    device.registers.set_vibration_intensity(1.0)
    device.registers.set_vibration_frequency(200)
    status_label.config(text="Status: High Heat & Strong Vibration")

def set_preset3():
    device.registers.set_thermal_mode(ThermalMode.MANUAL)
    device.registers.set_thermal_intensity(-0.5)
    device.registers.set_vibration_intensity(0.3)
    device.registers.set_vibration_frequency(100)
    status_label.config(text="Status: Light Cooling & Soft Vibration")

def stop():
    device.registers.set_thermal_mode(ThermalMode.OFF)
    device.registers.set_vibration_intensity(0.0)
    device.registers.set_global_led(0, 0, 0)
    status_label.config(text="Status: Off")

devices = discover_devices(3)  
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

def create_oval_button(canvas, text, command, rel_x, rel_y):
    width, height = canvas.winfo_width(), canvas.winfo_height()
    x, y = width * rel_x, height * rel_y
    button = canvas.create_oval(x, y, x+180, y+80, fill="#F5F5DC", outline="black", width=2)
    text_item = canvas.create_text(x+90, y+40, text=text, font=("Arial", 12, "bold"))
    canvas.tag_bind(button, "<Button-1>", lambda event: command())
    canvas.tag_bind(text_item, "<Button-1>", lambda event: command())
    return button, text_item

def resize_canvas(event):
    canvas.delete("all")
    create_oval_button(canvas, "Medium Heat & Vibration", set_preset1, 0.25, 0.2)
    create_oval_button(canvas, "High Heat & Strong Vibration", set_preset2, 0.25, 0.4)
    create_oval_button(canvas, "Light Cooling & Soft Vibration", set_preset3, 0.25, 0.6)
    create_oval_button(canvas, "Stop", stop, 0.25, 0.8)

status_label = tk.Label(tk_root, text="Status: Idle", font=("Arial", 14), bg="black", fg="white")
status_label.pack(pady=10)

canvas = tk.Canvas(tk_root, bg="black", highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)
tk_root.bind("<Configure>", resize_canvas)

tk_root.mainloop()
