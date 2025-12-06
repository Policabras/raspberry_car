#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from evdev import InputDevice, categorize, ecodes, list_devices

DEADZONE = 5      # Ignorar cambios pequeños en sticks
CENTER  = 127.0   # Centro aproximado de los joysticks
MAX_VAL = 255.0   # Valor máximo de ejes y gatillos


def encontrar_ds4():
    """Busca el DS4 principal, ignorando Touchpad y Motion Sensors."""
    for path in list_devices():
        dev = InputDevice(path)
        name = dev.name or ""
        if ("Wireless Controller" in name and
            "Touchpad" not in name and
            "Motion" not in name):
            return dev
    return None


def norm_stick(value):
    """0–255 -> -1..1 (0 en el centro)."""
    return (value - CENTER) / (MAX_VAL - CENTER) * 2.0


def norm_stick_invert_y(value):
    """Igual que norm_stick, pero arriba positivo."""
    return (CENTER - value) / (MAX_VAL - CENTER) * 2.0


def norm_trigger(value):
    """0–255 -> 0..1."""
    return value / MAX_VAL


def main():
    dev = encontrar_ds4()
    if dev is None:
        print("No se encontró el DS4 (Wireless Controller).")
        return

    print(f"Usando dispositivo: {dev.path} ({dev.name})")
    print("Mueve sticks / gatillos / D-Pad (Ctrl+C para salir)\n")

    last_axes = {}
    last_buttons = {}

    AXIS_NAMES = {
        ecodes.ABS_X:     "LX",
        ecodes.ABS_Y:     "LY",
        ecodes.ABS_RX:    "RX",
        ecodes.ABS_RY:    "RY",
        ecodes.ABS_Z:     "L2",
        ecodes.ABS_RZ:    "R2",
        ecodes.ABS_HAT0X: "DPAD_X",
        ecodes.ABS_HAT0Y: "DPAD_Y",
    }

    BUTTON_NAMES = {
        ecodes.BTN_SOUTH:  "X",
        ecodes.BTN_EAST:   "O",
        ecodes.BTN_WEST:   "CUADRADO",
        ecodes.BTN_NORTH:  "TRIANGULO",
        ecodes.BTN_TL:     "L1",
        ecodes.BTN_TR:     "R1",
        ecodes.BTN_THUMBL: "L3",
        ecodes.BTN_THUMBR: "R3",
        ecodes.BTN_SELECT: "SHARE",
        ecodes.BTN_START:  "OPTIONS",
        ecodes.BTN_MODE:   "PS",
    }

    try:
        dev.grab()
        grabbed = True
    except PermissionError:
        print("No se pudo hacer grab() (prueba con sudo).")
        grabbed = False

    try:
        for event in dev.read_loop():
            if event.type == ecodes.EV_SYN:
                continue

            # -------- BOTONES --------
            if event.type == ecodes.EV_KEY:
                code = event.code
                value = event.value
                if code in BUTTON_NAMES:
                    name = BUTTON_NAMES[code]
                    if last_buttons.get(code) != value:
                        last_buttons[code] = value
                        estado = "PRESIONADO" if value else "SUELTO"
                        print(f"[BOTON] {name}: {estado}")

            # -------- EJES --------
            elif event.type == ecodes.EV_ABS:
                code = event.code
                value = event.value

                if code not in AXIS_NAMES:
                    continue  # solo nos interesan estos ejes

                name = AXIS_NAMES[code]
                prev = last_axes.get(code, None)

                # Si ya teníamos un valor previo, aplicamos deadzone
                if prev is not None:
                    # Para sticks aplicamos deadzone
                    if name in ("LX", "LY", "RX", "RY"):
                        if abs(value - prev) < DEADZONE:
                            continue
                    # Si no cambió, no imprimimos
                    if value == prev:
                        continue

                # Guardar nuevo valor
                last_axes[code] = value

                # Normalizar según el tipo de eje
                if name in ("LX", "RX"):
                    norm = norm_stick(value)
                elif name in ("LY", "RY"):
                    norm = norm_stick_invert_y(value)
                elif name in ("L2", "R2"):
                    norm = norm_trigger(value)
                elif name in ("DPAD_X", "DPAD_Y"):
                    norm = value   # -1, 0, 1
                else:
                    norm = value

                print(f"[EJE] {name}: raw={value:3d}  norm={norm: .3f}")

    except KeyboardInterrupt:
        print("\nSaliendo...")
    finally:
        if grabbed:
            dev.ungrab()


if __name__ == "__main__":
    main()
