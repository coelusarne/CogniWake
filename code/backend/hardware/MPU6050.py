# backend/hardware/MPU6050.py
import math
import time
from smbus2 import SMBus

class MPU6050:
    """Class that calculates stationairy/lifted state from MPU6050 inputs and returns the state"""
    STATIONARY = "STATIONARY"
    LIFTED = "LIFTED"

    def __init__(self, addr=0x69, bus_id=1):
        self.addr = addr
        self.bus = SMBus(bus_id)
        self.bus.write_byte_data(self.addr, 0x6B, 0)

        time.sleep(0.2)

        self.base_x = None
        self.base_y = None
        self.base_z = None

        self.motion_counter = 0
        self.stable_counter = 0
        self.lifted = False

    def _read_word(self, reg):
        high = self.bus.read_byte_data(self.addr, reg)
        low = self.bus.read_byte_data(self.addr, reg + 1)
        value = (high << 8) + low

        if value >= 0x8000:
            value = -((65535 - value) + 1)

        return value

    def _read_magnitude(self):
        x = self._read_word(0x3B)
        y = self._read_word(0x3D)
        z = self._read_word(0x3F)
        return math.sqrt(x * x + y * y + z * z)

    def get_state(self):
        x = self._read_word(0x3B)
        y = self._read_word(0x3D)
        z = self._read_word(0x3F)

        if self.base_x is None:
            self.base_x = x
            self.base_y = y
            self.base_z = z
            return self.STATIONARY

        movement = (
            abs(x - self.base_x) +
            abs(y - self.base_y) +
            abs(z - self.base_z)
        )

        if movement > 6500:
            self.motion_counter = min(self.motion_counter + 1, 20)
            self.stable_counter = 0
        else:
            self.motion_counter = max(self.motion_counter - 1, 0)

            if self.lifted:
                self.stable_counter += 1

        if not self.lifted and self.motion_counter >= 8:
            self.lifted = True
            self.stable_counter = 0

        if self.lifted:
            # Require 10s of stability
            if self.stable_counter >= 100:
                self.lifted = False

                self.base_x = x
                self.base_y = y
                self.base_z = z

                self.motion_counter = 0
                self.stable_counter = 0

                return self.STATIONARY

            return self.LIFTED

        return self.STATIONARY

    def cleanup(self):
        self.bus.close()