from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from utils.websocket_manager import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID for the WebSocket connection"),
):
    """
    Simple WebSocket endpoint for subscribing to real-time events.

    Args:
        websocket: The WebSocket connection
        user_id: Unique identifier for the user
    """
    await manager.connect(websocket, user_id)

    try:
        # Keep connection alive and wait for disconnect
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)


@router.get("/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": len(manager.active_connections),
        "active_sessions": len(manager.session_participants),
        "connected_users": list(manager.active_connections.keys()),
    }
