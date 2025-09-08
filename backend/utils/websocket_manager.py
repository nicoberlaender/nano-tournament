from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""

    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store session participants for targeted messaging
        self.session_participants: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")

    def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")

        # Remove user from all sessions they were part of
        for session_id in list(self.session_participants.keys()):
            if user_id in self.session_participants[session_id]:
                self.session_participants[session_id].discard(user_id)
                if not self.session_participants[session_id]:
                    del self.session_participants[session_id]

    def add_to_session(self, session_id: str, user_id: str):
        """Add a user to a session for targeted messaging"""
        if session_id not in self.session_participants:
            self.session_participants[session_id] = set()
        self.session_participants[session_id].add(user_id)
        logger.info(f"User {user_id} added to session {session_id}")

    def remove_from_session(self, session_id: str, user_id: str):
        """Remove a user from a session"""
        if session_id in self.session_participants:
            self.session_participants[session_id].discard(user_id)
            if not self.session_participants[session_id]:
                del self.session_participants[session_id]

    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user"""
        websocket = self.active_connections[user_id]
        await websocket.send_text(
            json.dumps({**message, "timestamp": datetime.now().isoformat()})
        )

    async def send_session_message(self, message: dict, session_id: str):
        """Send a message to all participants in a session"""
        participants = list(self.session_participants[session_id])
        for user_id in participants:
            await self.send_personal_message(message, user_id)

    async def broadcast_message(self, message: dict):
        """Send a message to all connected users"""
        for user_id, websocket in self.active_connections.items():
            await websocket.send_text(
                json.dumps({**message, "timestamp": datetime.now().isoformat()})
            )

    def get_session_participants(self, session_id: str) -> List[str]:
        """Get list of participants in a session"""
        return list(self.session_participants.get(session_id, set()))

    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user is currently connected"""
        return user_id in self.active_connections


# Global connection manager instance
manager = ConnectionManager()
