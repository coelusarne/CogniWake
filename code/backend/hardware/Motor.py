# backend/hardware/Motor.py
# Imports
import RPi.GPIO as GPIO

class Motor:
    """
    simpel genoeg jonge
    """
    def __init__(self, pin):
        self.pin = pin

    def start(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def stop(self):
        GPIO.output(self.pin, GPIO.LOW)