# backend/routes/settings.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
import subprocess
from repositories.SettingsRepository import SettingsRepository
from services.NetworkService import NetworkService
from services.TimeService import TimeService
from datetime import datetime
from models.models import ThemePayload, NetworkPayload, TimeModePayload, ManualTimePayload, UsernamePayload, WeatherPayload, WeatherDetailsPayload
from repositories.AlarmRepository import AlarmRepository
from repositories.LogsRepository import LogsRepository
from repositories.MathRepository import MathRepository
SETTINGS_CLIENTS = []
settings_router = APIRouter(prefix="/api/v1/settings",tags=["settings"])

# streams settings changes
async def broadcast_settings(payload):
    dead = []
    for client in SETTINGS_CLIENTS:
        try:
            await client.send_text(json.dumps(payload))
        except Exception:
            dead.append(client)
    for client in dead:
        if client in SETTINGS_CLIENTS:
            SETTINGS_CLIENTS.remove(client)

@settings_router.get("/theme")
async def get_theme():
    return {"color": SettingsRepository.get_theme_color()}

@settings_router.post("/theme")
async def update_theme(payload: ThemePayload):
    SettingsRepository.set_theme_color(payload.color)
    await broadcast_settings({"type": "theme","color": payload.color})
    return {"success": True, "color": payload.color}

@settings_router.get("/network")
async def get_network():
    return NetworkService.get_config()

@settings_router.post("/network")
async def update_network(payload: NetworkPayload):
    if payload.network_mode == "wifi":
        NetworkService.connect_wifi(payload.ssid or "",payload.password)
    else:
        NetworkService.enable_access_point()
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.post("/network/refresh")
def refresh_networks():
    return {"networks": NetworkService.refresh_networks()}

@settings_router.post("/network/mode")
async def update_network_mode(payload: NetworkPayload):
    if payload.network_mode == "wifi":
        SettingsRepository.set_network_mode("wifi")
        success = NetworkService.auto_connect_known_network()
        if not success:
            NetworkService.enable_access_point()
    else:
        NetworkService.enable_access_point()
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.get("/time")
async def get_time():
    return TimeService.get_config()

@settings_router.post("/time")
async def update_time(payload: TimeModePayload):
    if payload.time_mode == "network":
        TimeService.enable_ntp()
        SettingsRepository.set_time_mode("ntp")
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.post("/manual-time")
async def update_manual_time(payload: ManualTimePayload):
    date_time = f"{payload.date} {payload.time}"
    TimeService.set_manual_time(date_time)
    SettingsRepository.set_time_mode("manual")
    SettingsRepository.set_manual_datetime(date_time)
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.get("/system-time")
async def get_system_time():
    return {"time": datetime.now().strftime("%H:%M")}

@settings_router.get("/username")
async def get_username():
    return {"username": SettingsRepository.get_username()}

@settings_router.post("/username")
async def update_username(payload: UsernamePayload):
    SettingsRepository.set_username(payload.username)
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.get("/weather")
async def get_weather():
    return {"weather": SettingsRepository.get_weather()}

@settings_router.post("/weather")
async def set_weather(payload: WeatherPayload):
    SettingsRepository.set_weather(payload.state)
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.get("/weather-details")
async def get_weather_details():
    return {"weather_details": SettingsRepository.get_weather_details()}

@settings_router.post("/weather-details")
async def set_weather_details(payload: WeatherDetailsPayload):
    city_country = f"{payload.city},{payload.country}"
    SettingsRepository.set_weather_details(city_country)
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.post("/clear-alarms")
async def clear_alarms():
    AlarmRepository.clear_alarms()
    LogsRepository.add_system_log("SETTINGS",f"Alarms cleared")
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.post("/clear-logs")
async def clear_logs():
    LogsRepository.clear_system_logs()
    LogsRepository.add_system_log("SETTINGS",f"Logs cleared")
    await broadcast_settings({"type": "refresh"})
    return {"success": True}

@settings_router.post("/reboot")
async def reboot_device():
    LogsRepository.add_system_log("SETTINGS",f"Device reboot")
    subprocess.Popen(["sudo", "reboot"])
    return {"success": True}

@settings_router.post("/poweroff")
async def poweroff_device():
    LogsRepository.add_system_log("SETTINGS",f"Device poweroff")
    subprocess.Popen(["sudo", "shutdown", "-h", "now"])
    return {"success": True}

@settings_router.post("/clear-history")
async def delete_history():
    MathRepository.delete_history()
    LogsRepository.add_system_log("SETTINGS",f"History cleared")
    await broadcast_settings({"type": "refresh"})
    return {"success": True}
    
@settings_router.websocket("/ws")
async def settings_ws(websocket: WebSocket):
    await websocket.accept()
    SETTINGS_CLIENTS.append(websocket)

    try:
        while True:
            await asyncio.sleep(3600)

    except WebSocketDisconnect:
        pass

    finally:
        if websocket in SETTINGS_CLIENTS:
            SETTINGS_CLIENTS.remove(websocket)
