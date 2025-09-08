from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from utils.websocket_manager import manager
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID for the WebSocket connection"),
):
    """
    WebSocket endpoint for real-time communication.

    Args:
        websocket: The WebSocket connection
        user_id: Unique identifier for the user

    Message Types Supported:
        - session_join: User joins a session
        - session_leave: User leaves a session
        - ping: Keep-alive ping
    """
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            message = json.loads(data)
            message_type = message.get("type")

            if message_type == "session_join":
                session_id = message.get("session_id")
                manager.add_to_session(session_id, user_id)
                # Notify other session participants
                await manager.send_session_message(
                    {
                        "type": "user_joined_session",
                        "user_id": user_id,
                        "session_id": session_id,
                    },
                    session_id,
                )

            elif message_type == "session_leave":
                session_id = message.get("session_id")
                manager.remove_from_session(session_id, user_id)
                # Notify other session participants
                await manager.send_session_message(
                    {
                        "type": "user_left_session",
                        "user_id": user_id,
                        "session_id": session_id,
                    },
                    session_id,
                )

            elif message_type == "ping":
                # Respond with pong for keep-alive
                await manager.send_personal_message({"type": "pong"}, user_id)

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
