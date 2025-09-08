from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional
import json
import logging
import asyncio
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class GamePhase(Enum):
    """Game phases for session state management"""
    LOBBY = "lobby"
    PROMPT = "prompt" 
    WAITING_FOR_CHARACTERS = "waiting_for_characters"
    BATTLE = "battle"
    RESULTS = "results"


class SessionState:
    """Track state for each game session"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.phase = GamePhase.LOBBY
        self.participants: Set[str] = set()
        self.characters_ready: Set[str] = set()
        self.created_at = datetime.now()


class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""

    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store session participants for targeted messaging
        self.session_participants: Dict[str, Set[str]] = {}
        # Store session states for game flow management
        self.session_states: Dict[str, SessionState] = {}

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
        
        # Initialize session state if it doesn't exist
        if session_id not in self.session_states:
            self.session_states[session_id] = SessionState(session_id)
        
        self.session_states[session_id].participants.add(user_id)
        logger.info(f"User {user_id} added to session {session_id}")

    def remove_from_session(self, session_id: str, user_id: str):
        """Remove a user from a session"""
        if session_id in self.session_participants:
            self.session_participants[session_id].discard(user_id)
            if not self.session_participants[session_id]:
                del self.session_participants[session_id]
        
        # Also remove from session state
        if session_id in self.session_states:
            self.session_states[session_id].participants.discard(user_id)
            self.session_states[session_id].characters_ready.discard(user_id)
            if not self.session_states[session_id].participants:
                del self.session_states[session_id]

    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user"""
        if user_id not in self.active_connections:
            logger.warning(f"User {user_id} is not connected, skipping message")
            return

        websocket = self.active_connections[user_id]
        try:
            await websocket.send_text(
                json.dumps({**message, "timestamp": datetime.now().isoformat()})
            )
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")
            # Remove the connection if it's stale
            self.disconnect(user_id)

    async def send_session_message(self, message: dict, session_id: str):
        """Send a message to all participants in a session"""
        if session_id not in self.session_participants:
            logger.warning(
                f"Session {session_id} has no participants, skipping message"
            )
            return

        participants = list(self.session_participants[session_id])
        for user_id in participants:
            await self.send_personal_message(message, user_id)

    async def broadcast_message(self, message: dict):
        """Send a message to all connected users"""
        # Create a copy of the items to avoid modification during iteration
        connections_copy = list(self.active_connections.items())
        for user_id, websocket in connections_copy:
            try:
                await websocket.send_text(
                    json.dumps({**message, "timestamp": datetime.now().isoformat()})
                )
            except Exception as e:
                logger.warning(f"Failed to broadcast message to user {user_id}: {e}")
                # Remove the connection if it's stale
                self.disconnect(user_id)

    def get_session_participants(self, session_id: str) -> List[str]:
        """Get list of participants in a session"""
        return list(self.session_participants.get(session_id, set()))

    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user is currently connected"""
        return user_id in self.active_connections

    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Get the current state of a session"""
        return self.session_states.get(session_id)

    def set_session_phase(self, session_id: str, phase: GamePhase):
        """Set the current phase for a session"""
        if session_id in self.session_states:
            self.session_states[session_id].phase = phase
            logger.info(f"Session {session_id} phase changed to {phase.value}")

    def mark_character_ready(self, session_id: str, user_id: str):
        """Mark a user's character as ready"""
        if session_id in self.session_states:
            self.session_states[session_id].characters_ready.add(user_id)

    def are_all_characters_ready(self, session_id: str) -> bool:
        """Check if all participants have ready characters"""
        if session_id not in self.session_states:
            return False
        
        state = self.session_states[session_id]
        return len(state.characters_ready) == len(state.participants) and len(state.participants) >= 2

    async def simulate_battle_completion(self, session_id: str):
        """Simulate battle completion with mocked results"""
        if session_id not in self.session_states:
            return
        
        # Mock battle for 3 seconds
        await asyncio.sleep(3)
        
        state = self.session_states[session_id]
        participants = list(state.participants)
        
        if len(participants) >= 2:
            # Mock winner selection
            import random
            winner_id = random.choice(participants)
            
            # Send results to all participants
            await self.send_session_message({
                "type": "results",
                "session_id": session_id,
                "winner_user_id": winner_id,
                "battle_script": "Epic battle between legendary fighters! The arena shook as powerful attacks were exchanged. In the end, one fighter emerged victorious through superior strategy and skill.",
                "battle_summary": f"An intense battle concluded with a decisive victory!"
            }, session_id)
            
            # Set phase to results
            self.set_session_phase(session_id, GamePhase.RESULTS)


# Global connection manager instance
manager = ConnectionManager()
