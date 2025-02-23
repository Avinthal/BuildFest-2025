from time import sleep
from datafeel.device import ThermalMode, LedMode, discover_devices

def main():
    devices = discover_devices(1)  # Discover a single Datafeel Dot
    if not devices:
        print("No devices found.")
        return
    
    device = devices[0]
    print("Device found:", device)
    
    # Set LED to red
    device.registers.set_led_mode(LedMode.GLOBAL_MANUAL)
    device.registers.set_global_led(255, 0, 0)  # Red color
    
    # Start heat and cold cycles
    for i in range(3):  # Repeat cycle 3 times
        print("Heating...")
        device.registers.set_thermal_mode(ThermalMode.OPEN_LOOP)
        device.registers.set_thermal_intensity(1.0)  # Max heat
        sleep(5)
        
        print("Cooling...")
        device.registers.set_thermal_intensity(-1.0)  # Max cool
        sleep(5)
    
    print("Disabling thermal control...")
    device.registers.set_thermal_mode(ThermalMode.OFF)
        
    # Keep LED red for a few seconds before turning off
    sleep(2)
    device.registers.set_global_led(0, 0, 0)  # Turn LED off

if __name__ == "__main__":
    main()
 
