#!/usr/bin/env python3

from evdev import InputDevice, list_devices

def main():
    devices = [InputDevice(path) for path in list_devices()]

    print("Input devices found:\n")
    for dev in devices:
        print(f"Route: {dev.path}")
        print(f"NAME: {dev.name}")
        print(f"Info: bustype={dev.info.bustype}, vendor={dev.info.vendor}, product={dev.info.product}")
        print("-" * 40)

if __name__ == "__main__":
    main()
