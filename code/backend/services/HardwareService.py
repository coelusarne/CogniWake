# backend/services/HardwareService.py
# Imports
import asyncio
import time
from datetime import datetime, timedelta
from repositories.LogsRepository import LogsRepository
from hardware.hardware_manager import buzzer, motor, mpu, rcwl

class HardwareService:
    def __init__(self):
        self.buzzer = buzzer
        self.motor = motor
        self.is_alarm_active = False
        self.is_muted = False
        self.alarm_task = None
        self.mpu = mpu
        self.rcwl = rcwl
        self.mpu_state = self.mpu.STATIONARY
        self.rcwl_state = self.rcwl.NO_MOTION
        self.sensor_listener_task = None
        self.rcwl_motion_since = None
        self.rcwl_snooze_triggered = False

    async def start_buzzer(self):
        if self.alarm_task and not self.alarm_task.done():
            return
        self.is_alarm_active = True
        self.is_muted = False
        self.rcwl_motion_since = None
        self.rcwl_snooze_triggered = False
        self.alarm_task = asyncio.create_task(self.run_alarm_stream())

    async def stop_buzzer(self, clear_alarm_state=True):
        self.is_alarm_active = False
        self.is_muted = False
        self.buzzer.stop()
        self.motor.stop()

        current_task = asyncio.current_task()
        if self.alarm_task and self.alarm_task is not current_task:
            try:
                await self.alarm_task
            except Exception:
                pass

        self.rcwl_motion_since = None
        self.rcwl_snooze_triggered = False

        if clear_alarm_state:
            try:
                from services.AlarmService import alarm_service
                if alarm_service.active_alarm_id is not None:
                    alarm_service.snoozed_until.pop(alarm_service.active_alarm_id, None)
                    alarm_service.active_alarm_id = None
            except Exception:
                pass

    async def run_alarm_stream(self):
        try:
            while self.is_alarm_active:
                if self.is_muted:
                    self.buzzer.stop()
                    self.motor.stop()
                    await asyncio.sleep(0.1)
                    continue

                self.motor.start()

                try:
                    await asyncio.to_thread(self.buzzer.beep, 0.15)
                finally:
                    self.motor.stop()

                await asyncio.sleep(0.3)

        finally:
            self.buzzer.stop()
            self.motor.stop()
            self.alarm_task = None

    async def start_sensor_listener(self):
        if self.sensor_listener_task is None or self.sensor_listener_task.done():
            self.sensor_listener_task = asyncio.create_task(self.sensor_listener())

    async def sensor_listener(self):
        while True:
            try:
                self.mpu_state = await asyncio.to_thread(self.mpu.get_state)
                rcwl_state = await asyncio.to_thread(self.rcwl.get_state)
                if rcwl_state is not None:
                    self.rcwl_state = rcwl_state

                if self.is_alarm_active:
                    if self.is_lifted():
                        self.is_muted = True
                        self.buzzer.stop()
                        self.motor.stop()
                        self.rcwl_motion_since = None
                        self.rcwl_snooze_triggered = False
                    else:
                        self.is_muted = False
                        if self.motion_detected():
                            if self.rcwl_motion_since is None:
                                self.rcwl_motion_since = time.monotonic()
                            elif not self.rcwl_snooze_triggered and time.monotonic() - self.rcwl_motion_since >= 3:
                                self.rcwl_snooze_triggered = True
                                try:
                                    from services.AlarmService import alarm_service
                                    alarm_id = alarm_service.active_alarm_id
                                    if alarm_id is not None:
                                        await alarm_service.snooze_active_alarm()
                                except Exception as e:
                                    LogsRepository.add_system_log("HARDWARE", f"Sensor listener error: {e}")
                        else:
                            self.rcwl_motion_since = None
                            self.rcwl_snooze_triggered = False
                else:
                    self.is_muted = False
                    self.rcwl_motion_since = None
                    self.rcwl_snooze_triggered = False

            except Exception as e:
                LogsRepository.add_system_log("HARDWARE", f"Sensor listener error: {e}")
            await asyncio.sleep(0.1)

    def is_lifted(self):
        return self.mpu_state == self.mpu.LIFTED

    def is_stationary(self):
        return self.mpu_state == self.mpu.STATIONARY

    def motion_detected(self):
        return self.rcwl_state == self.rcwl.MOTION

    def no_motion_detected(self):
        return self.rcwl_state == self.rcwl.NO_MOTION

    def get_sensor_states(self):
        return {
            "mpu": self.mpu_state,
            "rcwl": self.rcwl_state
        }

# Shared instance
hardware_service = HardwareService()