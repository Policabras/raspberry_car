from evdev import InputDevice, ecodes
import time
import RPi.GPIO as GPIO

DS4_PATH = "/dev/input/event4"
GPIO.setmode(GPIO.BCM)

L_IN1 = 17
L_IN2 = 27
L_ENA = 22 


GPIO.setup(L_ENA, GPIO.OUT)
GPIO.setup(L_IN1, GPIO.OUT)
GPIO.setup(L_IN2, GPIO.OUT)
pwm_L_ENA = GPIO.PWM(L_ENA, 1000)   # frecuencia 1000 Hz
pwm_L_ENA.start(0)

def main():
    dev = InputDevice(DS4_PATH)
    estado = {}

    try:
        dev.grab()
        print("Control listo, leyendo eventos...")

        for event in dev.read_loop():
            if event.type in (ecodes.EV_ABS, ecodes.EV_KEY):
                estado[event.code] = event.value

            # 🔹 Aquí empiezas a usar la lógica:
            logica_control(estado)

    except KeyboardInterrupt:
        print("\n[Ctrl+C] Saliendo...")

    except OSError as e:
        print(f"\n[OSError] Error con el control (¿se desconectó?): {e}")

    finally:
        try:
            dev.ungrab()
        except:
            pass
        detener_todo()
        print("Programa terminado correctamente.")


def logica_control(estado):
    # Ejemplo: joystick izquierdo en Y
    y = estado.get(ecodes.ABS_Y,127)  # 127 ~ centro

    if y > 140:
        left_axis_backward(y)
    elif y < 120:
        left_axis_forward(y)
    else:
        detener()

def left_axis_backward(y):
    GPIO.output(L_IN1, 1)
    GPIO.output(L_IN2, 0)
    pwm_ly_1 = (y-140)*100/115
    # enviar PWM al pin L_ENA
    pwm_L_ENA.ChangeDutyCycle(pwm_ly_1)

def left_axis_forward(y):
    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 1)
    pwm_ly_1 = (120 - y)*100/120
    pwm_L_ENA.ChangeDutyCycle(pwm_ly_1)

def detener():
    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 0)
    pwm_L_ENA.ChangeDutyCycle(0)

def detener_todo():
    # Aquí luego apagas motores, limpias GPIO, etc.
    print("Deteniendo todo.")
    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 0)
    pwm_L_ENA.ChangeDutyCycle(0)
    GPIO.cleanup()

if __name__ == "__main__":
    main()