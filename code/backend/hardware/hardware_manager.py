# backend/hardware/hardware_manager.py
# Imports
from hardware.Buzzer import Buzzer
from hardware.Motor import Motor
from hardware.RCWL0516 import RCWL0516
from hardware.Keypad import Keypad
from hardware.MPU6050 import MPU6050
from hardware.gpio_setup import (
    init_gpio,
    BUZZER_PIN,
    MOTOR_PIN,
    RCWL_PIN,
    KEYPAD_ROWS,
    KEYPAD_COLS
)
# init
init_gpio()

# create objects using pins
buzzer = Buzzer(BUZZER_PIN)
motor = Motor(MOTOR_PIN)
rcwl = RCWL0516(RCWL_PIN)
keypad = Keypad(KEYPAD_ROWS,KEYPAD_COLS)
mpu = MPU6050()