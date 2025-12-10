#!/usr/bin/env python3
import time

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, sh1106

I2C_ADDRESS = 0x3C  # Cambia si tu pantalla usa otra dirección

print("[OLED] Inicializando interfaz I2C...")
serial = i2c(port=1, address=I2C_ADDRESS)

device = None

# Intentar SSD1306 primero
try:
    device = ssd1306(serial)
    print("[OLED] Usando driver SSD1306")
except:
    try:
        device = sh1106(serial)
        print("[OLED] Usando driver SH1106")
    except:
        print("ERROR: No se pudo inicializar OLED")
        exit(1)

print(f"[OLED] Resolución: {device.width}x{device.height}")

device.clear()
device.show()

# ---------------- CARITA ENOJADA ----------------
with canvas(device) as draw:
    w, h = device.width, device.height
    cx, cy = w // 2, h // 2
    r = min(w, h) // 2 - 4  # radio con margen

    # Cabeza
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, fill=0)

    # Ojos — mismos que la carita feliz (rellenos blancos)
    eye_dx = r // 3
    eye_dy = -r // 4
    eye_r = max(2, r // 8)

    # Ojo izquierdo
    ex = cx - eye_dx
    ey = cy + eye_dy
    draw.ellipse((ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r), fill=255)

    # Ojo derecho
    ex = cx + eye_dx
    ey = cy + eye_dy
    draw.ellipse((ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r), fill=255)

    # **Cejas inclinadas** >:(
    brow_offset_y = eye_r * 2
    brow_length = eye_r * 3

    # Ceja izquierda inclinada hacia abajo
    draw.line(
        (cx - eye_dx - brow_length, cy + eye_dy - brow_offset_y,
         cx - eye_dx + brow_length, cy + eye_dy - brow_offset_y + 5),
        fill=255,
        width=2
    )

    # Ceja derecha inclinada hacia abajo (invertida)
    draw.line(
        (cx + eye_dx - brow_length, cy + eye_dy - brow_offset_y + 5,
         cx + eye_dx + brow_length, cy + eye_dy - brow_offset_y),
        fill=255,
        width=2
    )

    # Boca triste / enojada (arco invertido)
    mouth_r = (2 * r) // 3
    mouth_box = (cx - mouth_r, cy - mouth_r // 2, cx + mouth_r, cy + mouth_r)

    # arco invertido (como U al revés 😠)
    draw.arc(mouth_box, start=200, end=340, fill=255)

print("Carita ENOJADA dibujada en la OLED 😠🔥")
time.sleep(1)
