from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from utils.websocket_manager import manager, GamePhase
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID for the WebSocket connection"),
):
    """
    Enhanced WebSocket endpoint for handling game phase transitions.

    Args:
        websocket: The WebSocket connection
        user_id: Unique identifier for the user
    """
    await manager.connect(websocket, user_id)

    try:
        # Handle incoming messages from frontend
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_client_message(message, user_id)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from user {user_id}: {data}")
            except Exception as e:
                logger.error(f"Error handling message from user {user_id}: {e}")
    except WebSocketDisconnect:
        manager.disconnect(user_id)


async def handle_client_message(message: dict, user_id: str):
    """Handle incoming messages from the frontend client"""
    message_type = message.get("type")
    session_id = message.get("session_id")
    
    if message_type == "session_join":
        # Phase 1: Player joins session
        if session_id:
            manager.add_to_session(session_id, user_id)
            # Notify other players in the session (use user_id as name for now)
            await manager.send_session_message({
                "type": "user_joined_session",
                "user_id": user_id,
                "name": user_id,
                "session_id": session_id
            }, session_id)
            # Send current participants list to the joining user so they can see others in lobby
            await manager.send_personal_message({
                "type": "session_participants",
                "session_id": session_id,
                "participants": manager.get_session_participants(session_id)
            }, user_id)
            
    elif message_type == "session_leave":
        # Player leaves session
        if session_id:
            manager.remove_from_session(session_id, user_id)
            await manager.send_session_message({
                "type": "user_left_session", 
                "user_id": user_id,
                "session_id": session_id
            }, session_id)
            
    elif message_type == "start_round":
        # Phase 3: Host starts the game round
        if session_id:
            participants = manager.get_session_participants(session_id)
            if len(participants) >= 2 or True:  # Need at least 2 players TODO
                # Set session to prompt phase
                manager.set_session_phase(session_id, GamePhase.PROMPT)
                await manager.send_session_message({
                    "type": "round_start",
                    "session_id": session_id,
                    "message": "Round started! Create your characters."
                }, session_id)
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Need at least 2 players to start the round"
                }, user_id)
                
    elif message_type == "character_ready":
        # Phase 3: Player finished character generation
        if session_id:
            manager.mark_character_ready(session_id, user_id)
            
            # Check if all players are ready
            if manager.are_all_characters_ready(session_id):
                # Set phase to battle
                manager.set_session_phase(session_id, GamePhase.BATTLE)
                
                # Notify all characters are ready
                await manager.send_session_message({
                    "type": "all_characters_ready",
                    "session_id": session_id
                }, session_id)
                
                # Start the battle phase
                await manager.send_session_message({
                    "type": "battle_start",
                    "session_id": session_id,
                    "message": "All characters ready! Battle begins!"
                }, session_id)
                
                # Start async battle simulation (Phase 4)
                asyncio.create_task(manager.simulate_battle_completion(session_id))
            
    elif message_type == "ping":
        # Health check
        await manager.send_personal_message({
            "type": "pong"
        }, user_id)


@router.get("/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": len(manager.active_connections),
        "active_sessions": len(manager.session_participants),
        "connected_users": list(manager.active_connections.keys()),
    }
