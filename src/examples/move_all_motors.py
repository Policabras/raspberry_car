from evdev import InputDevice, ecodes
import time
import RPi.GPIO as GPIO

DS4_PATH = "/dev/input/event4"
GPIO.setmode(GPIO.BCM)

# Pin assignment
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

# Pin setup
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

# PWM Setup
pwm_L_ENA = GPIO.PWM(L_ENA, 1000)
pwm_L_ENB = GPIO.PWM(L_ENB, 1000)
pwm_R_ENA = GPIO.PWM(R_ENA, 1000)
pwm_R_ENB = GPIO.PWM(R_ENB, 1000)

pwm_L_ENA.start(0)
pwm_L_ENB.start(0)
pwm_R_ENA.start(0)
pwm_R_ENB.start(0)

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
        print(f"\n[OSError]Error with the controller (did it disconnect?): {e}")

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

    # Left axis logic
    if y > 140:
        left_axis_backward(y)
    elif y < 120:
        left_axis_forward(y)
    else:
        stop_left()

    # Right axis logic
    if x > 140 :
        right_axis_backward(x)
    elif x < 120:
        right_axis_forward(x)
    else:
        stop_right()

def left_axis_backward(y):
    GPIO.output(L_IN1, 1)
    GPIO.output(L_IN2, 0)
    GPIO.output(L_IN3, 1)
    GPIO.output(L_IN4, 0)
    pwm_ly_1 = (y-140)*100/115
    pwm_L_ENA.ChangeDutyCycle(pwm_ly_1)
    pwm_L_ENB.ChangeDutyCycle(pwm_ly_1)

def left_axis_forward(y):
    GPIO.output(L_IN1, 0)
    GPIO.output(L_IN2, 1)
    GPIO.output(L_IN3, 0)
    GPIO.output(L_IN4, 1)
    pwm_ly_1 = (120 - y)*100/120
    pwm_L_ENA.ChangeDutyCycle(pwm_ly_1)
    pwm_L_ENB.ChangeDutyCycle(pwm_ly_1)

def right_axis_backward(x):
    GPIO.output(R_IN1, 1)
    GPIO.output(R_IN2, 0)
    GPIO.output(R_IN3, 1)
    GPIO.output(R_IN4, 0)
    pwm_ry_1 = (x-140)*100/115
    pwm_R_ENA.ChangeDutyCycle(pwm_ry_1)
    pwm_R_ENB.ChangeDutyCycle(pwm_ry_1)

def right_axis_forward(x):
    GPIO.output(R_IN1, 0)
    GPIO.output(R_IN2, 1)
    GPIO.output(R_IN3, 0)
    GPIO.output(R_IN4, 1)
    pwm_ry_1 = (120 - x)*100/120
    pwm_R_ENA.ChangeDutyCycle(pwm_ry_1)
    pwm_R_ENB.ChangeDutyCycle(pwm_ry_1)

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
    pwm_L_ENB.ChangeDutyCycle(0)
    pwm_L_ENA.ChangeDutyCycle(0)


def stop_everything():
    print("Stopping everything.")
    GPIO.cleanup()

if __name__ == "__main__":
    main()