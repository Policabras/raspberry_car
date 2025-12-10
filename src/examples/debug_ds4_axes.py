#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import select
from evdev import InputDevice, ecodes

DS4_PATH = "/dev/input/event4"   # Ajusta si tu ruta cambia

def main():
    dev = InputDevice(DS4_PATH)

    print(f"Using device: {dev.path} ({dev.name})")
    print("Moving controls... (Ctrl+C para salir)\n")

    estado = {}

    # Tomar control exclusivo del dispositivo
    try:
        dev.grab()
    except PermissionError:
        print("No se pudo hacer grab() (probablemente falta sudo).")

    try:
        while True:
            # select() -> no bloqueante
            r, _, _ = select.select([dev], [], [], 0)

            if dev in r:
                for event in dev.read():
                    if event.type == ecodes.EV_ABS:
                        estado[event.code] = event.value
                    elif event.type == ecodes.EV_KEY:
                        estado[event.code] = event.value

            # Imprimir estado solo cada 100 ms
            print("------ ESTADO ACTUAL ------")
            for code, value in estado.items():

                # intentar identificar el nombre
                nombre = ecodes.ABS.get(code)
                if nombre is None:
                    nombre = ecodes.KEY.get(code, f"CODE_{code}")

                print(f"{nombre:12} = {value}")

            print("----------------------------\n")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Saliendo...")

    finally:
        try:
            dev.ungrab()
        except:
            pass


if __name__ == "__main__":
    main()
