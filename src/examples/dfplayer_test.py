#!/usr/bin/env python3
import time
import serial
from serial import SerialException

SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600
MAX_VOL = 15


def df_send(ser, cmd, param):
    """Send a raw frame to DFPlayer / MP3-TF-16P."""
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


def df_set_volume(ser, vol):
    """Set DFPlayer volume (0–30)."""
    vol = max(0, min(MAX_VOL, vol))
    df_send(ser, 0x06, vol)


def df_play_track(ser, num):
    """Play track by index (1 = 0001.mp3, 2 = 0002.mp3, ...)."""
    df_send(ser, 0x03, num)


def main():
    print("[DFPLAYER] Opening serial...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    print("[DFPLAYER] Waiting 3s for module to boot and mount SD...")
    time.sleep(3.0)

    print("[DFPLAYER] Setting volume...")
    df_set_volume(ser, 25)
    time.sleep(0.2)

    # Adjust this range depending on how many files you expect
    start_track = 1
    end_track = 30

    print(f"[SCAN] Scanning tracks {start_track} to {end_track}...")
    for track in range(start_track, end_track + 1):
        print(f"[SCAN] Playing track {track} ...")
        df_play_track(ser, track)
        # escucha unos segundos cada canción
        time.sleep(5)

    print("[SCAN] Done.")
    ser.close()


if __name__ == "__main__":
    main()
