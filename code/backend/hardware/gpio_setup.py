# backend/hardware/gpio_setup.py
# Imports
import RPi.GPIO as GPIO

# Component pin definitions
BUZZER_PIN = 20
MOTOR_PIN = 21
RCWL_PIN = 16
KEYPAD_ROWS = [17, 27, 22, 23]
KEYPAD_COLS = [24, 25, 5]

def init_gpio():
    """helper function to initialise all the GPIO things :D"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    GPIO.setup(BUZZER_PIN,GPIO.OUT,initial=GPIO.LOW)
    GPIO.setup(MOTOR_PIN,GPIO.OUT,initial=GPIO.LOW)
    GPIO.setup(RCWL_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN) # pulldown, sensor pullt high

    for row in KEYPAD_ROWS: # Inputs
        GPIO.setup(row,GPIO.OUT,initial=GPIO.HIGH)

    for col in KEYPAD_COLS: # Outputs
        GPIO.setup(col,GPIO.IN,pull_up_down=GPIO.PUD_UP)

def cleanup_gpio():
    GPIO.cleanup()