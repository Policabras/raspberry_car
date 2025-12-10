#!/usr/bin/env python3
import time
import serial

# Puerto serial del UART de la Raspberry
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

def send(cmd, param):
    # Arma el paquete para DFPlayer
    start = 0x7E
    version = 0xFF
    length = 0x06
    feedback = 0x00
    paramH = (param >> 8) & 0xFF
    paramL = param & 0xFF

    checksum = 0 - (version + length + cmd + feedback + paramH + paramL)
    checksum &= 0xFFFF
    checksumH = (checksum >> 8) & 0xFF
    checksumL = checksum & 0xFF
    end = 0xEF

    frame = bytes([
        start, version, length, cmd, feedback,
        paramH, paramL, checksumH, checksumL, end
    ])
    ser.write(frame)

# ---- INICIO DEL PROGRAMA ----

print("DFPlayer Mini: inicializando...")

time.sleep(1)

# VOLÚMEN (0 a 30)
send(0x06, 30)
time.sleep(0.2)

# REPRODUCIR LA PISTA 0001.mp3
send(0x03, 1)
print("Reproduciendo 0001.mp3")

# Esperar mientras suena
time.sleep(10)

print("Listo.")
ser.close()