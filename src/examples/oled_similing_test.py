#!/usr/bin/env python3
import time

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, sh1106

# Usa la misma dirección que te funcionó en el test (cámbiala si era 0x3D)
I2C_ADDRESS = 0x3C

print("[OLED] Inicializando interfaz I2C...")
serial = i2c(port=1, address=I2C_ADDRESS)

device = None

# Intentar primero SSD1306
try:
    device = ssd1306(serial)
    print("[OLED] Usando driver SSD1306")
except Exception as e:
    print("[OLED] Falló SSD1306:", e)
    print("[OLED] Probando SH1106...")
    try:
        device = sh1106(serial)
        print("[OLED] Usando driver SH1106")
    except Exception as e2:
        print("[OLED] También falló SH1106:", e2)
        print("[OLED] No se pudo inicializar la pantalla :(")
        exit(1)

print(f"[OLED] Resolución detectada: {device.width}x{device.height}")

# Limpiar pantalla
device.clear()
device.show()

# -------- DIBUJAR CARITA FELIZ --------
with canvas(device) as draw:
    w, h = device.width, device.height
    cx, cy = w // 2, h // 2
    r = min(w, h) // 2 - 4  # radio de la cara con margen

    # Cara (círculo grande)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, fill=0)

    # Ojos
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

    # Sonrisa (arco)
    mouth_r = (2 * r) // 3
    mouth_box = (cx - mouth_r, cy - mouth_r // 2, cx + mouth_r, cy + mouth_r)
    draw.arc(mouth_box, start=20, end=160, fill=255)

print("Carita feliz dibujada en la OLED 😄")
# La imagen se queda puesta hasta que otro programa la cambie
time.sleep(1)
