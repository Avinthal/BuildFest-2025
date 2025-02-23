import time
import math
import tkinter as tk
from tkinter import ttk
from datafeel.device import ThermalMode, LedMode, VibrationMode, discover_devices

presets = {}
running = False

def save_preset():
    """Saves user settings as a preset."""
    name = preset_entry.get().strip()
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
    """Loads a preset and fills in the entry fields."""
    name = preset_combobox.get()
    if name in presets:
        for entry, key in zip(
            [high_temp_entry, low_temp_entry, heat_duration_entry, cold_duration_entry, cycle_entry],
            ["high_temperature", "low_temperature", "heat_duration", "cold_duration", "cycles"]
        ):
            entry.delete(0, tk.END)
            entry.insert(0, presets[name][key])
        vib_combobox.set(presets[name]["vibration"])

def get_skin_temperature():
    """Continuously updates the skin temperature reading every 2 seconds."""
    for device in devices:
        try:
            temperature = device.get_skin_temperature()
            skin_temp_label.config(text=f"Skin Temperature: {temperature:.1f} °C")
        except Exception as e:
            skin_temp_label.config(text="Error reading temperature")
    root.after(2000, get_skin_temperature)  # Run again in 2 seconds

def apply_settings():
    """Applies user-selected settings and starts thermal + vibration cycles."""
    global running
    running = True
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

    def cycle_heat_cold(cycle_count):
        """Handles heating and cooling cycles."""
        global running
        if not running or cycle_count <= 0:
            stop()
            return
        for device in devices:
            try:
                if high_temp is not None:
                    device.registers.set_thermal_mode(ThermalMode.MANUAL)
                    intensity = max(-1.0, min(1.0, (high_temp - device.get_skin_temperature()) * 0.1))
                    device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
                device.registers.set_vibration_intensity(vibration_intensity)
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}")
        root.after(heat_duration * 1000, lambda: cycle_cold(cycle_count - 1))

    def cycle_cold(cycle_count):
        """Handles the cooling cycle."""
        global running
        if not running or cycle_count <= 0:
            stop()
            return
        for device in devices:
            try:
                if low_temp is not None:
                    device.registers.set_thermal_mode(ThermalMode.MANUAL)
                    intensity = max(-1.0, min(1.0, (low_temp - device.get_skin_temperature()) * 0.1))
                    device.registers.set_thermal_intensity(intensity)
                device.registers.set_vibration_mode(VibrationMode.MANUAL if vibration_intensity > 0 else VibrationMode.OFF)
                device.registers.set_vibration_intensity(vibration_intensity)
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}")
        root.after(cold_duration * 1000, lambda: cycle_heat_cold(cycle_count - 1))

    cycle_heat_cold(cycles)
    status_label.config(text=f"Status: Running {cycles} Cycles")

def stop():
    """Stops the active process and resets devices."""
    global running
    running = False
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

# Discover and initialize devices
devices = discover_devices(3)
if not devices:
    print("No devices found. Exiting.")
    exit()

for device in devices:
    device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
    device.registers.set_global_led(255, 0, 0)

# Tkinter UI Setup
root = tk.Tk()
root.title("Thermal Device Controller")
root.geometry("500x600")
root.configure(bg="black")

status_label = tk.Label(root, text="Status: Idle", fg="white", bg="black", font=("Arial", 12))
status_label.pack(pady=5)

skin_temp_label = tk.Label(root, text="Skin Temperature: -- °C", fg="white", bg="black")
skin_temp_label.pack(pady=5)
get_skin_temperature()

# UI Components
preset_label = tk.Label(root, text="Preset Name:", fg="white", bg="black")
preset_label.pack()
preset_entry = tk.Entry(root)
preset_entry.pack()

preset_combobox = ttk.Combobox(root, values=[], state="readonly")
preset_combobox.pack(pady=5)

# Temperature & Duration Entries
entries = [
    ("Set High Temperature (°C):", high_temp_entry := tk.Entry(root)),
    ("Set Low Temperature (°C):", low_temp_entry := tk.Entry(root)),
    ("Heat Duration (seconds):", heat_duration_entry := tk.Entry(root)),
    ("Cold Duration (seconds):", cold_duration_entry := tk.Entry(root)),
    ("Number of Cycles:", cycle_entry := tk.Entry(root))
]
for label, entry in entries:
    tk.Label(root, text=label, fg="white", bg="black").pack()
    entry.pack()

vib_label = tk.Label(root, text="Vibration Strength:", fg="white", bg="black")
vib_label.pack()
vib_combobox = ttk.Combobox(root, values=["Off", "Low", "Medium", "High"], state="readonly")
vib_combobox.pack(pady=5)
vib_combobox.current(0)

apply_button = tk.Button(root, text="Apply Settings", command=apply_settings)
apply_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop", command=stop)
stop_button.pack(pady=5)

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
