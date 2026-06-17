# backend/app.py
print("app loaded(debug)")
import asyncio
import socketio
import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.alarms import alarms_router
from routes.hardware import hardware_router, start_keypad_scanner
from routes.settings import settings_router
from routes.logs import logs_router

from hardware.gpio_setup import init_gpio, cleanup_gpio

from services.AlarmService import alarm_service
from services.NetworkService import NetworkService
from services.HardwareService import hardware_service
from repositories.SettingsRepository import SettingsRepository
from repositories.LogsRepository import LogsRepository


sio = socketio.AsyncServer(
    cors_allowed_origins='*',
    async_mode='asgi',
    logger=True
    )

@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    LogsRepository.add_system_log("SYSTEM", "Started")
    try:
        NetworkService._cached_networks = (NetworkService.scan_networks())
    except Exception as e:
        print(f"network scan failed: {e}")
    asyncio.create_task(start_keypad_scanner())
    if SettingsRepository.get_network_mode() == "ap":
        NetworkService.enable_access_point()
    else:
        NetworkService.auto_connect_known_network()
    await hardware_service.start_sensor_listener()
    await alarm_service.start(sio)
    
    yield
# app
app = FastAPI(lifespan=lifespan_manager)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# routers
app.include_router(alarms_router)
app.include_router(hardware_router)
app.include_router(settings_router)
app.include_router(logs_router)
# sio app 
sio_app = socketio.ASGIApp(sio, app)

@app.get('/')
async def root():
    return {'status': 'Backend running'}

@sio.event
async def connect(sid, environ):
    print(f'[Socket.IO] Connected: {sid}')
    await sio.emit(
        'B2F_connected',
        {
            'status': 'connected'
        },
        to=sid
    )

# main loop
if __name__ == '__main__':
    init_gpio() # gpio init
    uvicorn.run(
        'app:sio_app',
        host='0.0.0.0',
        port=5000,
        reload=False
    )
    cleanup_gpio() # cleanup on exit

