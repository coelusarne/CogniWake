# backend/routes/hardware.py
# Imports
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from hardware.hardware_manager import keypad
from tests.hardware_test import ACTIVE_TESTS, test_buzzer, test_motor, test_rcwl, test_mpu
from repositories.LogsRepository import LogsRepository
hardware_router = APIRouter(prefix='/api/v1/hardware',tags=['Hardware'])
TEST_MAP = {
    'buzzer': test_buzzer,
    'motor': test_motor,
    'rcwl0516': test_rcwl,
    'mpu6050': test_mpu
}

keypad_clients = set()

def _next_item(generator):
    try:
        return True, next(generator)
    except StopIteration:
        return False, None
    
# Subscribable consant keypad stream
async def start_keypad_scanner():
    async def scanner():
        last_key = None
        while True:
            key = keypad.scan()
            if key and key != last_key:
                dead = []
                for client in keypad_clients:
                    try:
                        await client.send_text(f"PRESS:{key}")
                    except Exception:
                        dead.append(client)
                for client in dead:
                    keypad_clients.discard(client)
                last_key = key
            elif not key and last_key:
                dead = []
                for ws in keypad_clients:
                    try:
                        await ws.send_text(f"RELEASE:{last_key}")
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    keypad_clients.discard(ws)
                last_key = None
            await asyncio.sleep(0.02)
    asyncio.create_task(scanner())

# Websocket to subscribe to the keypad scream(for inside frontend)
@hardware_router.websocket('/keypad/live')
async def keypad_live(websocket: WebSocket):
    await websocket.accept()
    keypad_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(3600)
    except WebSocketDisconnect:
        pass
    finally:
        keypad_clients.discard(websocket)
# Websocket for keypad hardware test
@hardware_router.websocket('/keypad/ws')
async def keypad_test_ws(websocket: WebSocket):
    await websocket.accept()
    keypad_clients.add(websocket)
    LogsRepository.add_system_log("SYSTEM", f"Keypad test started")
    try:
        while True:
            await asyncio.sleep(3600)
    except WebSocketDisconnect:
        pass
    finally:
        keypad_clients.discard(websocket)
# Websocket for hardware tests
@hardware_router.websocket('/{test_name}/ws')
async def hardware_test_ws(websocket: WebSocket, test_name: str):
    print("WS entered")
    await websocket.accept()
    print("WS ACCEPT")
    LogsRepository.add_system_log("SYSTEM", f"{test_name} test started")
    test_func = TEST_MAP.get(test_name)
    if not test_func:
        await websocket.send_text(f'ERR: Unknown: {test_name}')
        await websocket.close(code=1008)
        return
    generator = test_func()
    try:
        while True:
            has_item, chunk = await asyncio.to_thread(_next_item, generator)
            if not has_item:
                break
            if chunk is None:
                continue
            await websocket.send_text(str(chunk).rstrip('\n'))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(f'Error: {e}')
        except Exception:
            pass
    finally:
        ACTIVE_TESTS[test_name] = False
        try:
            if hasattr(generator, 'close'):
                generator.close()
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass

# Hardware test stream stop
@hardware_router.post('/{test_name}/stop')
async def stop_test(test_name: str):
    ACTIVE_TESTS[test_name] = False
    return {'ok': True}

