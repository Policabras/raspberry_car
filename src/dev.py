from evdev import InputDevice, ecodes
import time
import pigpio

DS4_PATH = "/dev/input/event4"
PWM_FREQ = 20000  # 20 kHz

# ------------ INITIALIZE pigpio ------------
pi = pigpio.pi()
if not pi.connected:
    raise SystemExit("Unable to connect to pigpiod. Did you run 'sudo pigpiod'?")
    # NOTA: LUEGO PROGRAMAR QUE PIGPIOD SE INICIE AUTOMÁTICAMENTE AL INICIAR EL SISTEMA

# ------------ LEFT MOTOR PINS ------------
L_IN1 = 17
L_IN2 = 27
L_IN3 = 10
L_IN4 = 9
L_ENA = 13 
L_ENB = 19

# ------------ RIGHT MOTOR PINS ------------
R_IN1 = 23
R_IN2 = 24
R_IN3 = 25
R_IN4 = 8
R_ENA = 18
R_ENB = 12

# ------------ PIN SETUP ------------
for pin in [L_IN1, L_IN2, L_IN3, L_IN4, R_IN1, R_IN2, R_IN3, R_IN4]:
    pi.set_mode(pin, pigpio.OUTPUT)
    pi.write(pin, 0)

# ------------ PWM SETUP ------------
for pin in [L_ENA, L_ENB, R_ENA, R_ENB]:
    pi.hardware_PWM(pin, PWM_FREQ, 0)

def main():
    dev = InputDevice(DS4_PATH)
    estado = {}

    try:
        dev.grab()
        print("DS4 ready, reading events...")

        # Main loop
        for event in dev.read_loop():
            if event.type in (ecodes.EV_ABS, ecodes.EV_KEY):
                estado[event.code] = event.value

            logica_control(estado)

    except KeyboardInterrupt:
        print("\n[Ctrl+C] Leaving...")

    except OSError as e:
        print(f"\n[OSError] Error con el control (¿se desconectó?): {e}")

    finally:
        try:
            dev.ungrab()
        except:
            pass
        stop_everything()
        print("Program finished successfully.")

def logica_control(estado):
    y = estado.get(ecodes.ABS_Y,127) # Left y axis
    x = estado.get(ecodes.ABS_RY,127) # Right y axis

    # ---------- LEFT SIDE ----------
    if y > 140:
        left_axis_backward(y)
    elif y < 120:
        left_axis_forward(y)
    else:
        stop_left()

    # ---------- RIGHT SIDE ----------
    if x > 140 :
        right_axis_backward(x)
    elif x < 120:
        right_axis_forward(x)
    else:
        stop_right()

# ---------- MOTION FUNCTIONS ----------
def left_axis_backward(y):
    pi.write(L_IN1, 1)
    pi.write(L_IN2, 0)
    pi.write(L_IN3, 1)
    pi.write(L_IN4, 0)

    pwm_ly = int((y - 140) * 1_000_000 / 115)

    pi.hardware_PWM(L_ENA, PWM_FREQ, pwm_ly)
    pi.hardware_PWM(L_ENB, PWM_FREQ, pwm_ly)

def left_axis_forward(y):
    pi.write(L_IN1, 0)
    pi.write(L_IN2, 1)
    pi.write(L_IN3, 0)
    pi.write(L_IN4, 1)

    pwm_ly = int((120 - y) * 1_000_000 / 120)

    pi.hardware_PWM(L_ENA, PWM_FREQ, pwm_ly)
    pi.hardware_PWM(L_ENB, PWM_FREQ, pwm_ly)

def right_axis_backward(x):
    pi.write(R_IN1, 1)
    pi.write(R_IN2, 0)
    pi.write(R_IN3, 1)
    pi.write(R_IN4, 0)

    pwm_ry = int((x - 140) * 1_000_000 / 115)

    pi.hardware_PWM(R_ENA, PWM_FREQ, pwm_ry)
    pi.hardware_PWM(R_ENB, PWM_FREQ, pwm_ry)

def right_axis_forward(x):
    pi.write(R_IN1, 0)
    pi.write(R_IN2, 1)
    pi.write(R_IN3, 0)
    pi.write(R_IN4, 1)

    pwm_ry = int((120 - x) * 1_000_000 / 120)

    pi.hardware_PWM(R_ENA, PWM_FREQ, pwm_ry)
    pi.hardware_PWM(R_ENB, PWM_FREQ, pwm_ry)

def stop_left():
    for pin in [L_IN1, L_IN2, L_IN3, L_IN4]:
        pi.write(pin, 0)
    pi.hardware_PWM(L_ENA, PWM_FREQ, 0)
    pi.hardware_PWM(L_ENB, PWM_FREQ, 0)

def stop_right():
    for pin in [R_IN1, R_IN2, R_IN3, R_IN4]:
        pi.write(pin, 0)
    pi.hardware_PWM(R_ENA, PWM_FREQ, 0)
    pi.hardware_PWM(R_ENB, PWM_FREQ, 0)

def stop_everything():
    print("Stopping everything.")
    stop_left()
    stop_right()
    pi.stop()

if __name__ == "__main__":
    main()