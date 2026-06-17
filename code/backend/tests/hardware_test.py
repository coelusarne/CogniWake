# backend/tests/hardware_test.py
# Imports
import time

from hardware.hardware_manager import (buzzer, motor, rcwl, keypad, mpu)
ACTIVE_TESTS = {}

# Buzzer
def test_buzzer():
    """Go through a few frequencies as long as test stream active"""
    ACTIVE_TESTS['buzzer'] = True
    try:
        yield 'Start buzzer test\n'
        while ACTIVE_TESTS['buzzer']:
            for freq in [500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]:
                if not ACTIVE_TESTS['buzzer']: # exit 
                    break
                buzzer.start(freq, 25)
                time.sleep(0.5)
                if not ACTIVE_TESTS['buzzer']: # exit
                    break
                buzzer.stop()
                time.sleep(0.5)
    finally:
        buzzer.stop()

# Motor
def test_motor():
    ACTIVE_TESTS['motor'] = True
    try:
        yield 'Starting motor test\n'
        while ACTIVE_TESTS['motor']:
            motor.start()
            time.sleep(0.5)
            motor.stop()
            time.sleep(0.5)
    finally:
        motor.stop()

# RCWL 0516 Radar
def test_rcwl():
    last_state = None
    try:
        while True:
            current_state = rcwl.detected()
            if current_state != last_state:
                if current_state:
                    yield 'MOTION\n'
                else:
                    yield 'NO_MOTION\n'
                last_state = current_state
            time.sleep(0.05)
    except GeneratorExit:
        pass
    finally:
        pass
        
# MPU6050 Gyro
def test_mpu():
    last_state = None
    try:
        while True:
            state = mpu.get_state()
            if state != last_state:
                yield f'{state}\n'
                last_state = state
            time.sleep(0.15)
    except GeneratorExit:
        pass
    finally:
        pass