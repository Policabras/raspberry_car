#!/usr/bin/env python3
from evdev import InputDevice, ecodes
import time
import RPi.GPIO as GPIO
import os

DS4_PATH = "/dev/input/event4"
GPIO.setmode(GPIO.BCM)

# ---------------- PINES ----------------
L_IN1 = 17
L_IN2 = 27
L_IN3 = 10
L_IN4 = 9
L_ENA = 13 
L_ENB = 19

R_IN1 = 23
R_IN2 = 24
R_IN3 = 25
R_IN4 = 8
R_ENA = 18
R_ENB = 12

# ---------------- SETUP GPIO ----------------
GPIO.setup(L_IN1, GPIO.OUT)
GPIO.setup(L_IN2, GPIO.OUT)
GPIO.setup(L_IN3, GPIO.OUT)
GPIO.setup(L_IN4, GPIO.OUT)
GPIO.setup(L_ENA, GPIO.OUT)
GPIO.setup(L_ENB, GPIO.OUT)

GPIO.setup(R_IN1, GPIO.OUT)
GPIO.setup(R_IN2, GPIO.OUT)
GPIO.setup(R_IN3, GPIO.OUT)
GPIO.setup(R_IN4, GPIO.OUT)
GPIO.setup(R_ENA, GPIO.OUT)
GPIO.setup(R_ENB, GPIO.OUT)

# ---------------- PWM ----------------
pwm_L_ENA = GPIO.PWM(L_ENA, 1000)
pwm_L_ENB = GPIO.PWM(L_ENB, 1000)
pwm_R_ENA = GPIO.PWM(R_ENA, 1000)
pwm_R_ENB = GPIO.PWM(R_ENB, 1000)

pwm_L_ENA.start(0)
pwm_L_ENB.start(0)
pwm_R_ENA.start(0)
pwm_R_ENB.start(0)

# ======================================================
#                    DS4 HELPERS
# ======================================================

def esperar_ds4(path, retry_delay=1.0):
    """Espera hasta que el DS4 exista y se pueda abrir sin tronar."""
    while True:
        try:
            dev = InputDevice(path)
            print(f"[DS4] Detectado en {path}: {dev.name}")
            return dev
        except FileNotFoundError:
            print(f"[DS4] {path} no encontrado. Conecta el control...")
        except OSError as e:
            print(f"[DS4] Dispositivo no listo ({e}). Esperando...")

        time.sleep(retry_delay)


def check_shutdown_combo(estado):
    # SHARE y OPTIONS en DS4: códigos 314 y 315
    share   = estado.get(314, 0)
    options = estado.get(315, 0)

    if share == 1 and options == 1:
        print("[POWER] SHARE + OPTIONS presionados. Apagando Raspberry...")
        os.system("sudo shutdown -h now")


# ======================================================
#                        MAIN
# ======================================================

def main():
    estado = {}
    dev = None

    try:
        while True:
            # Esperar hasta que haya DS4 disponible
            dev = esperar_ds4(DS4_PATH)

            try:
                dev.grab()
                print("DS4 ready, reading events...")

                for event in dev.read_loop():
                    if event.type in (ecodes.EV_ABS, ecodes.EV_KEY):
                        estado[event.code] = event.value

                    logica_control(estado)
                    check_shutdown_combo(estado)

            except OSError as e:
                # Control desconectado / error de I/O
                print(f"\n[DS4] Se desconectó o falló: {e}")
                stop_left()
                stop_right()
                print("[DS4] Esperando otra vez al control...")
                time.sleep(1)

            finally:
                if dev is not None:
                    try:
                        dev.ungrab()
                    except:
                        pass
                    dev = None

    except KeyboardInterrupt:
        print("\n[Ctrl+C] Leaving...")

    finally:
        stop_everything()
        print("Program finished successfully.")


# ======================================================
#                  LÓGICA DE CONTROL
# ======================================================

def logica_control(estado):
    y  = estado.get(ecodes.ABS_Y, 127)   # Left stick Y
    x  = estado.get(ecodes.ABS_RY, 127)  # Right stick Y
    lz = estado.get(ecodes.ABS_Z, 0)     # L2
    rz = estado.get(ecodes.ABS_RZ, 0)    # R2

    # ---------- PRIORIDAD: MOVIMIENTO LATERAL ----------
    if lz > 0:
        left_lateral_movement(lz)
        return

    if rz > 0:
        right_lateral_movement(rz)
        return

    # ---------- SIN LATERAL: ADELANTE / ATRÁS ----------
    # Lado izquierdo
    if y > 140:
        left_axis_backward(y)
    elif y < 120:
        left_axis_forward(y)
    else:
        stop_left()

    # Lado derecho
    if x > 140:
        right_axis_backward(x)
    elif x < 120:
        right_axis_forward(x)
    else:
        stop_right()


# ======================================================
#                   FUNCIONES DE MOVIMIENTO
# ======================================================

def left_axis_backward(y):
    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 1)
    GPIO.output(L_IN3, 0)
    GPIO.output(L_IN4, 1)
    pwm_ly_1 = (y - 140) * 100 / 115
    pwm_L_ENA.ChangeDutyCycle(pwm_ly_1)
    pwm_L_ENB.ChangeDutyCycle(pwm_ly_1)

def left_axis_forward(y):
    GPIO.output(L_IN1, 1)
    GPIO.output(L_IN2, 0)
    GPIO.output(L_IN3, 1)
    GPIO.output(L_IN4, 0)
    pwm_ly_1 = (120 - y) * 100 / 120
    pwm_L_ENA.ChangeDutyCycle(pwm_ly_1)
    pwm_L_ENB.ChangeDutyCycle(pwm_ly_1)

def right_axis_backward(x):
    GPIO.output(R_IN1, 1)
    GPIO.output(R_IN2, 0)
    GPIO.output(R_IN3, 0)
    GPIO.output(R_IN4, 1)
    pwm_ry_1 = (x - 140) * 100 / 115
    pwm_R_ENA.ChangeDutyCycle(pwm_ry_1)
    pwm_R_ENB.ChangeDutyCycle(pwm_ry_1)

def right_axis_forward(x):
    GPIO.output(R_IN1, 0)
    GPIO.output(R_IN2, 1)
    GPIO.output(R_IN3, 1)
    GPIO.output(R_IN4, 0)
    pwm_ry_1 = (120 - x) * 100 / 120
    pwm_R_ENA.ChangeDutyCycle(pwm_ry_1)
    pwm_R_ENB.ChangeDutyCycle(pwm_ry_1)

def left_lateral_movement(lz):
    # Config de pines para desplazamiento lateral hacia la izquierda
    GPIO.output(R_IN1, 1)
    GPIO.output(R_IN2, 0)
    GPIO.output(R_IN3, 1)
    GPIO.output(R_IN4, 0)

    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 1)
    GPIO.output(L_IN3, 1)
    GPIO.output(L_IN4, 0)

    pwm_z = int(lz * 100 / 255)
    pwm_R_ENA.ChangeDutyCycle(pwm_z)
    pwm_R_ENB.ChangeDutyCycle(pwm_z)
    pwm_L_ENA.ChangeDutyCycle(pwm_z)
    pwm_L_ENB.ChangeDutyCycle(pwm_z)

def right_lateral_movement(rz):
    # Config de pines para desplazamiento lateral hacia la derecha
    GPIO.output(R_IN1, 0)
    GPIO.output(R_IN2, 1)
    GPIO.output(R_IN3, 0)
    GPIO.output(R_IN4, 1)

    GPIO.output(L_IN1, 1)
    GPIO.output(L_IN2, 0)
    GPIO.output(L_IN3, 0)
    GPIO.output(L_IN4, 1)

    pwm_z = int(rz * 100 / 255)
    pwm_R_ENA.ChangeDutyCycle(pwm_z)
    pwm_R_ENB.ChangeDutyCycle(pwm_z)
    pwm_L_ENA.ChangeDutyCycle(pwm_z)
    pwm_L_ENB.ChangeDutyCycle(pwm_z)

# ======================================================
#                    STOP FUNCTIONS
# ======================================================

def stop_right():
    GPIO.output(R_IN1, 0)
    GPIO.output(R_IN2, 0)
    GPIO.output(R_IN3, 0)
    GPIO.output(R_IN4, 0)
    pwm_R_ENA.ChangeDutyCycle(0)
    pwm_R_ENB.ChangeDutyCycle(0)

def stop_left():
    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 0)
    GPIO.output(L_IN3, 0)
    GPIO.output(L_IN4, 0)
    pwm_L_ENA.ChangeDutyCycle(0)
    pwm_L_ENB.ChangeDutyCycle(0)

def stop_everything():
    print("Stopping everything.")
    stop_left()
    stop_right()
    GPIO.cleanup()

# ======================================================

if __name__ == "__main__":
    main()
