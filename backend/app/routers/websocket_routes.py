"""
WebSocket Router

Real-time game broadcasts and per-user notification channels.
"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..managers.websocket_manager import manager as websocket_manager

logger = logging.getLogger("app.routers.websocket_routes")

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):  # type: ignore
    await websocket_manager.connect(websocket, game_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.broadcast(f"Message from client for game {game_id}: {data}", game_id)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, game_id)
        await websocket_manager.broadcast(f"A client disconnected from game {game_id}", game_id)


@router.websocket("/ws/user/{player_id}")
async def user_websocket_endpoint(websocket: WebSocket, player_id: int):  # type: ignore
    """WebSocket endpoint for per-user notifications (match updates, etc.)."""
    await websocket_manager.connect_user(websocket, player_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"type": "pong", "data": data}))
    except WebSocketDisconnect:
        websocket_manager.disconnect_user(websocket, player_id)
