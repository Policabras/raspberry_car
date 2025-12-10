import pigpio
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

PIN = 22  # elige un GPIO libre (o uno de tus ENA/ENB si quieres probar con el driver)
L_IN1 = 17
L_IN2 = 27

GPIO.setup(L_IN1, GPIO.OUT)
GPIO.setup(L_IN2, GPIO.OUT)

pi = pigpio.pi()
if not pi.connected:
    print("Unable to connect to pigpiod. Are you running sudo pigpiod?")
    exit(1)

pi.set_PWM_frequency(PIN, 20000)  # 20 kHz
print("Real frequency:", pi.get_PWM_frequency(PIN))

for duty in range(0, 256, 64):
    print("Duty:", duty)
    pi.set_PWM_dutycycle(PIN, duty)
    GPIO.output(L_IN1, 1)
    GPIO.output(L_IN2, 0)
    time.sleep(2)

pi.set_PWM_dutycycle(PIN, 0)
pi.stop()
