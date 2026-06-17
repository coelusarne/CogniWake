# backend/hardware/Keypad.py
# Imports
import time
import RPi.GPIO as GPIO

class Keypad:
    """
    Class for mapping the input of keypad :D
    """
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.layout = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['*', '0', '#']
        ]
        self.last_key = None
        self.last_time = 0
        for row in self.rows:
            GPIO.setup(row, GPIO.OUT)
            GPIO.output(row, GPIO.HIGH)

        for col in self.cols:
            GPIO.setup(col,GPIO.IN,pull_up_down=GPIO.PUD_UP)

    def scan(self):
        now = time.time()

        for row_index, row_pin in enumerate(self.rows):
            for r in self.rows:
                GPIO.output(r, GPIO.HIGH)

            GPIO.output(row_pin, GPIO.LOW)
            time.sleep(0.002)

            for col_index, col_pin in enumerate(self.cols):
                if GPIO.input(col_pin) == GPIO.LOW:
                    key = self.layout[row_index][col_index]
                    # debounce the new key
                    if ( key != self.last_key or now - self.last_time > 0.05):
                        self.last_key = key
                        self.last_time = now

                    return key

        self.last_key = None
        return None