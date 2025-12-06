import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

led_pin = 17
GPIO.setup(led_pin, GPIO.OUT)

# Frecuencia de PWM (recomendado para LED)
pwm = GPIO.PWM(led_pin, 1000)  # 1000 Hz
pwm.start(0)  # Inicia con 0% de potencia

print("Intentando PWM...")
try:
    while True:
        # Aumentar brillo gradualmente
        for duty in range(0, 101, 1):  # 0% a 100%
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.02)  # Velocidad del cambio

        # Disminuir brillo gradualmente
        for duty in range(100, -1, -1):  # 100% a 0%
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.02)

except KeyboardInterrupt:
    pass

finally:
    pwm.stop()
    GPIO.cleanup()
    print("PWM detenido y GPIO liberado")
