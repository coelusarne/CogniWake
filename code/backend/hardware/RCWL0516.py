# backend/hardware/RCWL0516 .py
import time
import RPi.GPIO as GPIO

class RCWL0516:
    """Class for using the microwave sensos"""
    MOTION = "MOTION"
    NO_MOTION = "NO_MOTION"

    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self._last_state = False
        self._last_change = time.time()

    def detected(self):
        return GPIO.input(self.pin) == GPIO.HIGH

    def get_state(self):
        detected = self.detected()
        now = time.time()

        # debounce
        if detected != self._last_state:
            self._last_state = detected
            self._last_change = now

        # stabilisatie delay
        if now - self._last_change < 0.15:
            return None

        if detected:
            return self.MOTION

        return self.NO_MOTION