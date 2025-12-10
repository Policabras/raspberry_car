#!/usr/bin/env python3
import os
import time
import serial
from serial import SerialException

import RPi.GPIO as GPIO
from evdev import InputDevice, ecodes

# ======================================================
#                     GENERAL CONFIG
# ======================================================

DS4_PATH = "/dev/input/event4"
GPIO.setmode(GPIO.BCM)

# ======================================================
#                     DFPLAYER CONFIG
# ======================================================

SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600
DFPLAYER_MAX_VOL = 30

df_ser = None  # global DFPlayer handler


def df_open_serial():
    """Open DFPlayer serial port if not already open."""
    global df_ser

    if df_ser is None or not df_ser.is_open:
        print("[DFPLAYER] Opening serial...")
        df_ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)


def df_send(cmd, param):
    """
    Sends a raw command frame to DFPlayer.
    Handles auto-reconnection if the serial port fails.
    """
    global df_ser
    df_open_serial()

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

    try:
        df_ser.write(frame)
    except (SerialException, OSError) as e:
        print(f"[DFPLAYER] Write error: {e}. Reopening serial...")
        try:
            df_ser.close()
        except Exception:
            pass
        df_ser = None
        time.sleep(0.2)
        df_open_serial()


def df_set_volume(vol):
    """Set DFPlayer volume (0–30)."""
    vol = max(0, min(DFPLAYER_MAX_VOL, vol))
    df_send(0x06, vol)


def df_play_track(num):
    """
    Play a track by number:
    e.g., 0001.mp3 → 1, 0002.mp3 → 2.
    """
    df_send(0x03, num)


# ======================================================
#                       GPIO PINS
# ======================================================

# LEFT SIDE
L_IN1 = 17
L_IN2 = 27
L_IN3 = 10
L_IN4 = 9
L_ENA = 13
L_ENB = 19

# RIGHT SIDE
R_IN1 = 23
R_IN2 = 24
R_IN3 = 25
R_IN4 = 8
R_ENA = 18
R_ENB = 12

PWM_FREQ = 1000  # Hz

# Pin groups
LEFT_DIR_PINS = [L_IN1, L_IN2, L_IN3, L_IN4]
RIGHT_DIR_PINS = [R_IN1, R_IN2, R_IN3, R_IN4]
LEFT_PWM_PINS = [L_ENA, L_ENB]
RIGHT_PWM_PINS = [R_ENA, R_ENB]

ALL_PINS = LEFT_DIR_PINS + RIGHT_DIR_PINS + LEFT_PWM_PINS + RIGHT_PWM_PINS

# PWM handlers
pwm_L_ENA = None
pwm_L_ENB = None
pwm_R_ENA = None
pwm_R_ENB = None


def setup_gpio():
    """Configure all GPIO pins and initialize PWM modules."""
    global pwm_L_ENA, pwm_L_ENB, pwm_R_ENA, pwm_R_ENB

    # Set all pins as OUTPUT
    for pin in ALL_PINS:
        GPIO.setup(pin, GPIO.OUT)

    # Initialize PWM objects
    pwm_L_ENA = GPIO.PWM(L_ENA, PWM_FREQ)
    pwm_L_ENB = GPIO.PWM(L_ENB, PWM_FREQ)
    pwm_R_ENA = GPIO.PWM(R_ENA, PWM_FREQ)
    pwm_R_ENB = GPIO.PWM(R_ENB, PWM_FREQ)

    for pwm in (pwm_L_ENA, pwm_L_ENB, pwm_R_ENA, pwm_R_ENB):
        pwm.start(0)


# ======================================================
#                    DS4 HELPERS
# ======================================================

BTN_SHARE = 314
BTN_OPTIONS = 315


def esperar_ds4(path, retry_delay=1.0):
    """Wait until the DS4 appears and can be accessed without errors."""
    while True:
        try:
            dev = InputDevice(path)
            print(f"[DS4] Detected: {dev.name}")
            return dev
        except FileNotFoundError:
            print(f"[DS4] {path} not found. Connect controller...")
        except OSError as e:
            print(f"[DS4] Device not ready ({e}). Retrying...")

        time.sleep(retry_delay)


def check_shutdown_combo(estado):
    """Shutdown Raspberry Pi when SHARE + OPTIONS are pressed."""
    share = estado.get(BTN_SHARE, 0)
    options = estado.get(BTN_OPTIONS, 0)

    if share == 1 and options == 1:
        print("[POWER] SHARE + OPTIONS detected → Shutting down...")
        os.system("sudo shutdown -h now")


# ======================================================
#                    CONTROL LOGIC
# ======================================================

def logica_control(estado):
    """Main robot control logic based on DS4 input state."""
    y = estado.get(ecodes.ABS_Y, 127)
    x = estado.get(ecodes.ABS_RY, 127)
    lz = estado.get(ecodes.ABS_Z, 0)
    rz = estado.get(ecodes.ABS_RZ, 0)

    # ---------- LATERAL MOVEMENT PRIORITY ----------
    if lz > 0:
        left_lateral_movement(lz)
        return

    if rz > 0:
        right_lateral_movement(rz)
        return

    # ---------- FORWARD / BACKWARD ----------
    # Left side
    if y > 140:
        left_axis_backward(y)
    elif y < 120:
        left_axis_forward(y)
    else:
        stop_left()

    # Right side
    if x > 140:
        right_axis_backward(x)
    elif x < 120:
        right_axis_forward(x)
    else:
        stop_right()


# ======================================================
#              LINEAR MOVEMENT FUNCTIONS
# ======================================================

def left_axis_backward(y):
    """Move both left motors backward."""
    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 1)
    GPIO.output(L_IN3, 0)
    GPIO.output(L_IN4, 1)

    pwm_val = (y - 140) * 100 / 115
    pwm_L_ENA.ChangeDutyCycle(pwm_val)
    pwm_L_ENB.ChangeDutyCycle(pwm_val)


def left_axis_forward(y):
    """Move both left motors forward."""
    GPIO.output(L_IN1, 1)
    GPIO.output(L_IN2, 0)
    GPIO.output(L_IN3, 1)
    GPIO.output(L_IN4, 0)

    pwm_val = (120 - y) * 100 / 120
    pwm_L_ENA.ChangeDutyCycle(pwm_val)
    pwm_L_ENB.ChangeDutyCycle(pwm_val)


def right_axis_backward(x):
    """Move both right motors backward."""
    GPIO.output(R_IN1, 1)
    GPIO.output(R_IN2, 0)
    GPIO.output(R_IN3, 0)
    GPIO.output(R_IN4, 1)

    pwm_val = (x - 140) * 100 / 115
    pwm_R_ENA.ChangeDutyCycle(pwm_val)
    pwm_R_ENB.ChangeDutyCycle(pwm_val)


def right_axis_forward(x):
    """Move both right motors forward."""
    GPIO.output(R_IN1, 0)
    GPIO.output(R_IN2, 1)
    GPIO.output(R_IN3, 1)
    GPIO.output(R_IN4, 0)

    pwm_val = (120 - x) * 100 / 120
    pwm_R_ENA.ChangeDutyCycle(pwm_val)
    pwm_R_ENB.ChangeDutyCycle(pwm_val)


# ======================================================
#                 LATERAL MECANUM MOVEMENT
# ======================================================

def _trigger_to_pwm(val):
    """Convert trigger value (0–255) to PWM duty cycle (0–100)."""
    return int(val * 100 / 255)


def left_lateral_movement(lz):
    """Move robot LEFT using mecanum wheels (L2)."""
    GPIO.output(R_IN1, 1)
    GPIO.output(R_IN2, 0)
    GPIO.output(R_IN3, 1)
    GPIO.output(R_IN4, 0)

    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 1)
    GPIO.output(L_IN3, 1)
    GPIO.output(L_IN4, 0)

    pwm = _trigger_to_pwm(lz)
    pwm_R_ENA.ChangeDutyCycle(pwm)
    pwm_R_ENB.ChangeDutyCycle(pwm)
    pwm_L_ENA.ChangeDutyCycle(pwm)
    pwm_L_ENB.ChangeDutyCycle(pwm)


def right_lateral_movement(rz):
    """Move robot RIGHT using mecanum wheels (R2)."""
    GPIO.output(R_IN1, 0)
    GPIO.output(R_IN2, 1)
    GPIO.output(R_IN3, 0)
    GPIO.output(R_IN4, 1)

    GPIO.output(L_IN1, 1)
    GPIO.output(L_IN2, 0)
    GPIO.output(L_IN3, 0)
    GPIO.output(L_IN4, 1)

    pwm = _trigger_to_pwm(rz)
    pwm_R_ENA.ChangeDutyCycle(pwm)
    pwm_R_ENB.ChangeDutyCycle(pwm)
    pwm_L_ENA.ChangeDutyCycle(pwm)
    pwm_L_ENB.ChangeDutyCycle(pwm)


# ======================================================
#                       STOP FUNCTIONS
# ======================================================

def _stop_side(dir_pins, pwm_a, pwm_b):
    """Generic helper to stop one side of the robot."""
    for pin in dir_pins:
        GPIO.output(pin, 0)
    pwm_a.ChangeDutyCycle(0)
    pwm_b.ChangeDutyCycle(0)


def stop_left():
    """Stop all left motors."""
    _stop_side(LEFT_DIR_PINS, pwm_L_ENA, pwm_L_ENB)


def stop_right():
    """Stop all right motors."""
    _stop_side(RIGHT_DIR_PINS, pwm_R_ENA, pwm_R_ENB)


def stop_everything():
    """Stop the entire robot and clean GPIO."""
    print("Stopping everything...")
    stop_left()
    stop_right()
    GPIO.cleanup()


# ======================================================
#                         MAIN
# ======================================================

def main():
    estado = {}
    dev = None

    setup_gpio()

    time.sleep(1.5)
    df_set_volume(30)

    try:
        while True:
            dev = esperar_ds4(DS4_PATH)

            try:
                dev.grab()
                print("DS4 ready — reading events...")

                for event in dev.read_loop():
                    # Update state
                    if event.type in (ecodes.EV_ABS, ecodes.EV_KEY):
                        estado[event.code] = event.value

                    # ---------- D-PAD AUDIO ----------
                    if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_HAT0Y:
                        if event.value == -1:
                            print("[AUDIO] ↑ → Track 1")
                            df_play_track(1)
                        elif event.value == 1:
                            print("[AUDIO] ↓ → Track 3")
                            df_play_track(3)

                    elif event.type == ecodes.EV_ABS and event.code == ecodes.ABS_HAT0X:
                        if event.value == -1:
                            print("[AUDIO] ← → Track 4")
                            df_play_track(4)
                        elif event.value == 1:
                            print("[AUDIO] → → Track 2")
                            df_play_track(2)

                    # ---------- ROBOT CONTROL ----------
                    logica_control(estado)
                    check_shutdown_combo(estado)

            except OSError as e:
                print(f"\n[DS4] Controller disconnected: {e}")
                stop_left()
                stop_right()
                print("[DS4] Waiting for reconnection...")
                time.sleep(1)

            finally:
                if dev is not None:
                    try:
                        dev.ungrab()
                    except Exception:
                        pass
                    dev = None

    except KeyboardInterrupt:
        print("\n[Ctrl+C] Exiting...")

    finally:
        stop_everything()
        try:
            if df_ser is not None and df_ser.is_open:
                df_ser.close()
        except Exception:
            pass
        print("Program terminated.")


# ======================================================
if __name__ == "__main__":
    main()
