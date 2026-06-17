# backend/routes/alarms.py
# Imports
import asyncio
import time
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from repositories.MathRepository import MathRepository
from repositories.AlarmRepository import AlarmRepository
from models.models import AlarmPayload, VerifyQueryPayload
from services.AlarmService import alarm_service
from utils.math_generator import generate_math_query
from repositories.LogsRepository import LogsRepository
alarms_router = APIRouter(prefix='/api/v1/alarms', tags=['alarms'])

connected_ui_clients = set()
active_math_answers = {}  # map alarm id to answer

@alarms_router.get('/')
async def get_alarms():
    return {'alarms': AlarmRepository.read_alarms()}

@alarms_router.post('/')
async def create_alarm(payload: AlarmPayload):
    try:
        result = AlarmRepository.create_alarm(
            payload.timestamp,
            payload.label,
            payload.difficultyID,
            payload.days_bitmask,
            payload.active,
            payload.snooze_enabled,
            payload.snooze_minutes
        )
        await alarm_service.reload()
        LogsRepository.add_system_log("ALARMS",f"Alarm created: {result}")
        return {'success': True, 'result': result}
    except Exception as e:
        print(f'Failed creating alarm: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@alarms_router.delete('/{alarm_id}')
async def delete_alarm(alarm_id: int):
    try:
        result = AlarmRepository.delete_alarm(alarm_id)
        await alarm_service.reload()
        LogsRepository.add_system_log("ALARMS",f"Alarm deleted: {alarm_id}")
        return {'success': True, 'result': result}
    except Exception as e:
        print(f'Failed deleting alarm {alarm_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@alarms_router.put('/{alarm_id}')
async def update_alarm(alarm_id: int, payload: AlarmPayload):
    try:
        result = AlarmRepository.update_alarm(
            alarm_id,
            payload.timestamp,
            payload.label,
            payload.difficultyID,
            payload.days_bitmask,
            payload.active,
            payload.snooze_enabled,
            payload.snooze_minutes
        )
        await alarm_service.reload()
        LogsRepository.add_system_log("ALARMS",f"Alarm updated: {alarm_id}")
        return {'success': True, 'result': result}
    except Exception as e:
        print(f'Failed updating alarm {alarm_id}: {e}')
        raise HTTPException(status_code=500, detail=str(e))

# alarm trigger stream
@alarms_router.websocket("/live")
async def alarm_live_ws(websocket: WebSocket):
    await websocket.accept()
    connected_ui_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(3600)  # keepopen
    except WebSocketDisconnect:
        connected_ui_clients.remove(websocket)

# query generation 
@alarms_router.get("/math-query/{alarm_id}")
async def get_math_query(alarm_id: int):
    if alarm_id in active_math_answers:
        return {"question": active_math_answers[alarm_id]["question"]}
    alarms = AlarmRepository.read_alarms()
    target_alarm = next((a for a in alarms if a.get("alarmID") == alarm_id), None)
    difficulty = int(target_alarm.get("difficultyID", 2)) if target_alarm else 2
    question_str, correct_answer = generate_math_query(difficulty)
    log_id = MathRepository.create_log(alarm_id, question_str)

    active_math_answers[alarm_id] = {
        "question": question_str,
        "answer": correct_answer,
        "log_id": log_id,
        "started": time.time(),
        "attempt": 0
    }
    return {"question": question_str}

# query verification
@alarms_router.post("/verify-query")
async def verify_query(payload: VerifyQueryPayload):
    try:
        alarm_id = int(payload.alarmID)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid alarm format.")
    
    if alarm_id not in active_math_answers:
        raise HTTPException(status_code=400, detail="No query found for alarm.")

    entry = active_math_answers[alarm_id]
    entry["attempt"] += 1 
    is_correct = payload.user_answer == entry["answer"]
    MathRepository.add_answer(
        entry["log_id"],
        entry["attempt"],
        str(payload.user_answer),
        int(is_correct)
    )
    if is_correct:
        elapsed = int(time.time() - entry["started"])
        MathRepository.complete_log(entry["log_id"],elapsed)
        del active_math_answers[alarm_id]
        alarm_service.snoozed_once.discard(alarm_id)
        try:
            from services.HardwareService import hardware_service
            await hardware_service.stop_buzzer()
        except Exception as e:
            LogsRepository.add_system_log("ALARMS",f"ERROR: {e}")
        return {"success": True, "message": "Alarm deactivated."}
    else:
        return {"success": False, "message": "Incorrect."}
    
# dashboard statistics
@alarms_router.get("/dashboard")
async def dashboard():
    next_alarm = MathRepository.get_next_alarm()
    average_tries = MathRepository.get_average_attempts()
    average_solve_time = MathRepository.get_average_solve_time()
    first_try_percentage = MathRepository.get_first_try_percentage()
    return {
        "next_alarm": next_alarm if next_alarm else 0,
        "average_tries": average_tries["average_attempts"] if average_tries else 0,
        "average_solve_time": average_solve_time["average_time"] if average_solve_time else 0,
        "first_try_percentage": first_try_percentage["percentage"] if first_try_percentage else 0,
        "history": MathRepository.get_recent_history()
    }