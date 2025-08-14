import json
from typing import Any

from bson.objectid import ObjectId
from core.config import client_motor
from fastapi import (
    Depends, HTTPException, WebSocket, WebSocketDisconnect, status
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials

    # Truy vấn trực tiếp MongoDB
    information = await client_motor["core_admin"]["chatbot_api_keys"].find_one(
        {"key": token}
    )

    if not information:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Xóa các field không cần
    for field in ["_id", "createdAt", "updatedAt"]:
        information.pop(field, None)

    return information


async def get_current_user_websocket(websocket: WebSocket) -> dict:
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        raise WebSocketDisconnect(code=4001, reason="Missing authentication token")
    
    # Query trực tiếp MongoDB
    information = await client_motor["core_admin"]["chatbot_api_keys"].find_one(
        {"key": token}
    )

    if not information:
        await websocket.close(code=4001, reason="Invalid authentication credentials")
        raise WebSocketDisconnect(code=4001, reason="Invalid authentication credentials")

    for field in ["_id", "createdAt", "updatedAt"]:
        information.pop(field, None)

    return information
