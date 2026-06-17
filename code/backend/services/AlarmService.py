# backend/services/AlarmService.py
# Imports
import asyncio
from datetime import datetime, timedelta
from repositories.AlarmRepository import AlarmRepository
from repositories.LogsRepository import LogsRepository

class AlarmService:
    """Manages alarms"""
    def __init__(self):
        self.sio = None
        self._task = None
        self._reload_event = asyncio.Event()
        self._triggered_alarms = {}
        self.active_alarm_id = None
        self.active_alarm = None
        self.snoozed_until = {}
        self.snoozed_once = set()

    async def start(self, sio):
        """Start background alarm loop"""
        self.sio = sio
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run())

    async def reload(self):
        """Called when any changes are made to alarms"""
        self._reload_event.set()
        try:
            payload = json.dumps({
                "event": "reload"
            })

            for client in list(connected_ui_clients):
                try:
                    await client.send_text(payload)
                except Exception:
                    pass

        except Exception:
            pass

    async def run(self):
        while True:
            try:
                alarms = AlarmRepository.read_alarms()
                active_alarms = [alarm for alarm in alarms if alarm.get("active", 1) == 1]

                if not active_alarms:
                    self._reload_event.clear()
                    try:
                        await asyncio.wait_for(self._reload_event.wait(), timeout=60)
                    except asyncio.TimeoutError:
                        pass
                    continue

                now = datetime.now()
                current_day_bit = 1 << ((now.weekday() + 1) % 7) # Bitmask

                for alarm in active_alarms:
                    alarm_time_raw = alarm["timestamp"]

                    # hour/min from type
                    if isinstance(alarm_time_raw, datetime):
                        alarm_hour = alarm_time_raw.hour
                        alarm_minute = alarm_time_raw.minute
                        dt_parsed = alarm_time_raw
                    else:
                        # fallback parse
                        if "T" in alarm_time_raw:
                            time_str = alarm_time_raw.split("T")[1][:5]
                        elif " " in alarm_time_raw:
                            time_str = alarm_time_raw.split(" ")[1][:5]
                        else:
                            time_str = alarm_time_raw[:5]
                        alarm_hour, alarm_minute = map(int, time_str.split(":"))

                        try:
                            dt_parsed = datetime.fromisoformat(alarm_time_raw.replace('Z', ''))
                        except Exception:
                            dt_parsed = None

                    bitmask = alarm.get("days_bitmask", 0)

                    # eval day match
                    if bitmask > 0:
                        is_today = (bitmask & current_day_bit) > 0
                    else:
                        #ot fallback
                        if dt_parsed:
                            is_today = (dt_parsed.year == now.year and
                                        dt_parsed.month == now.month and
                                        dt_parsed.day == now.day)
                        else:
                            is_today = True

                    alarm_id = alarm["alarmID"]

                    if alarm_id in self.snoozed_until:
                        if now < self.snoozed_until[alarm_id]:
                            continue
                        del self.snoozed_until[alarm_id]
                        self._triggered_alarms.pop(alarm_id, None)
                        await self.trigger_alarm(alarm)
                        continue

                    is_time_match = (alarm_hour == now.hour and alarm_minute == now.minute)
                    current_minute_marker = f"{now.year}-{now.month}-{now.day}_{now.hour}:{now.minute}"

                    if is_today and is_time_match:
                        if self._triggered_alarms.get(alarm_id) != current_minute_marker:
                            self._triggered_alarms[alarm_id] = current_minute_marker
                            await self.trigger_alarm(alarm)

                self._reload_event.clear()
                try:
                    await asyncio.wait_for(self._reload_event.wait(), timeout=1)
                except asyncio.TimeoutError:
                    pass

            except Exception as e:
                await asyncio.sleep(5)

    async def trigger_alarm(self, alarm):
        alarm_id = alarm["alarmID"]
        self.active_alarm_id = alarm_id
        self.active_alarm = alarm
        LogsRepository.add_system_log("ALARMS", f"{alarm_id} triggered")
        try:
            from services.HardwareService import hardware_service
            await hardware_service.start_buzzer()
        except Exception as e:
            LogsRepository.add_system_log("ALARMS",f"Failed to start buzzer")

        # trigger event to listening clients
        try:
            from routes.alarms import connected_ui_clients
            import json

            payload = json.dumps({
                "event": "alarm_triggered",
                "alarmID": alarm_id,
                "label": alarm.get("label", "Alarm!")
            })

            for client in list(connected_ui_clients):
                try:
                    await client.send_text(payload)
                except Exception:
                    pass
        except Exception as e:
            LogsRepository.add_system_log("ALARMS",f"Could not trigger {alarm_id}")

        #keep fallback sio broadcast
        if self.sio:
            try:
                await self.sio.emit(
                    "alarm_triggered",
                    {
                        "alarmID": alarm_id,
                        "label": alarm.get("label", "")
                    }
                )
            except Exception:
                pass

    async def snooze_active_alarm(self):
        print("snooze")
        alarm_id = self.active_alarm_id
        alarm = self.active_alarm or {}
        if alarm_id is None:
            return
        if alarm_id in self.snoozed_once:
            return
        snooze_enabled = int(alarm.get("snooze_enabled"))
        if not snooze_enabled:
            return

        snooze_minutes = int(alarm.get("snooze_minutes"))
        print(snooze_minutes)
        from services.HardwareService import hardware_service
        from routes.alarms import active_math_answers, connected_ui_clients
        import json

        await hardware_service.stop_buzzer(clear_alarm_state=False)

        self.snoozed_until[alarm_id] = datetime.now() + timedelta(minutes=snooze_minutes)
        self.snoozed_once.add(alarm_id)
        self._triggered_alarms.pop(alarm_id, None)

        payload = json.dumps({
            "event": "alarm_snoozed",
            "alarmID": alarm_id,
            "snooze_until": self.snoozed_until[alarm_id].isoformat()
        })
        for client in list(connected_ui_clients):
            try:
                await client.send_text(payload)
            except Exception:
                connected_ui_clients.discard(client)

        LogsRepository.add_system_log("ALARMS",f"{alarm_id} snoozed")
        self.active_alarm_id = None
        self.active_alarm = None

alarm_service = AlarmService()