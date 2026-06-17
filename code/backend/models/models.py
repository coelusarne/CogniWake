# backend/models/models.py
# Imports
from pydantic import BaseModel

class DTOAlarm(BaseModel):
    timestamp: str
    label: str
    difficultyID: int

class DTOHardwareTest(BaseModel):
    test_name: str

class AlarmStatus(BaseModel):
    alarmID: int
    active: int
    
class AlarmPayload(BaseModel):
    timestamp: str
    label: str
    difficultyID: int
    days_bitmask: int
    active: int
    snooze_enabled: int = 1
    snooze_minutes: int = 5

class ThemePayload(BaseModel):
    color: str

class NetworkPayload(BaseModel):
    network_mode: str
    ssid: str | None = None
    password: str | None = None

class TimeModePayload(BaseModel):
    time_mode: str

class ManualTimePayload(BaseModel):
    date: str
    time: str

class UsernamePayload(BaseModel):
    username: str

class VerifyQueryPayload(BaseModel):
    alarmID: int
    user_answer: int
class WeatherPayload(BaseModel):
    state: str
class WeatherDetailsPayload(BaseModel):
    city: str
    country: str