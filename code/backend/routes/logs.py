# backend/routes/logs.py
# Imports
from fastapi import APIRouter
from repositories.LogsRepository import LogsRepository

logs_router = APIRouter(
    prefix="/api/v1/logs",
    tags=["logs"]
)

@logs_router.get("/")
async def get_logs():
    return { "logs": LogsRepository.get_system_logs() }
