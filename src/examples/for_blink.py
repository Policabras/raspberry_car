#!/usr/bin/env python3
#
#  for_blink.py
#  
#  Copyright 2025 Unknown <pytito-4@raspberry>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  


import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

led_pin = 17

# Configurar el pin como salida
GPIO.setup(led_pin, GPIO.OUT)
for i in range(1, 6):
    # Encender el LED
    GPIO.output(led_pin, True)
    print("LED encendida")

    # Mantener encendido 5 segundos
    time.sleep(1)

    # Apagar LED
    GPIO.output(led_pin, False)
    print("LED apagada")
    time.sleep(1)

# Liberar los pines
GPIO.cleanup()
