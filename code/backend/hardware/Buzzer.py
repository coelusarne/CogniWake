# backend/hardware/buzzer.py
# Imports
import RPi.GPIO as GPIO

class Buzzer:
    """Class for operating passive buzzer."""
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 1000)
        self.pwm.start(0)
    
    def start(self, frequency=1000, duty_cycle=5):
        self.pwm.ChangeFrequency(frequency)
        self.pwm.ChangeDutyCycle(duty_cycle)

    def stop(self):
        self.pwm.ChangeDutyCycle(0)
        GPIO.output(self.pin, GPIO.LOW)

    def beep(self, duration=0.15, frequency=8000, duty_cycle=50):
        self.start(frequency, duty_cycle)
        import time 
        time.sleep(duration)
        self.stop()

    def cleanup(self):
        self.stop()
        self.pwm.stop()