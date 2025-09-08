from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from models.database import Session, User, Character, get_db
from utils.image_generation import generate_fight_condition
from utils.websocket_manager import manager
import uuid

router = APIRouter(prefix="/session", tags=["session"])


class CreateSessionRequest(BaseModel):
    user_id: str


class JoinSessionRequest(BaseModel):
    user_id: str


class SessionResponse(BaseModel):
    session_id: str
    player1_id: str
    player2_id: str | None
    created_at: datetime
    status: str
    condition: str | None
    battle_video_url: str | None = None
    has_confrontation_image: bool = False

    class Config:
        from_attributes = True


@router.post("/", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest, db: AsyncSession = Depends(get_db)
):
    """
    Create a new game session with the requesting user as player 1.

    Args:
        request: Contains user_id of the player creating the session

    Returns:
        SessionResponse: The created session with ID, players, timestamp, and status
    """
    # Check if user exists, create if not
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(id=request.user_id)
        db.add(user)
        await db.flush()  # Flush to get the user in the session

    # Generate fight condition
    fight_condition = generate_fight_condition()

    # Create new session with user as player 1
    new_session = Session(
        player1_id=request.user_id,
        status="waiting",
        condition=fight_condition,
    )

    # Add to database
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return SessionResponse(
        session_id=new_session.id,
        player1_id=new_session.player1_id,
        player2_id=new_session.player2_id,
        created_at=new_session.created_at,
        status=new_session.status,
        condition=new_session.condition,
        battle_video_url=new_session.battle_video_url,
        has_confrontation_image=bool(new_session.confrontation_image),
    )


@router.post("/join/{session_id}", response_model=SessionResponse)
async def join_session(
    session_id: str, request: JoinSessionRequest, db: AsyncSession = Depends(get_db)
):
    """
    Join an existing game session as player 2.

    Args:
        session_id: The ID of the session to join
        request: Contains user_id of the player joining the session

    Returns:
        SessionResponse: The updated session with both players

    Raises:
        HTTPException: If session doesn't exist, is full, or other errors occur
    """
    # Check if session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if session is already full
    if session.player2_id is not None:
        raise HTTPException(status_code=400, detail="Session is already full")

    # Check if user is trying to join their own session
    if session.player1_id == request.user_id:
        raise HTTPException(status_code=400, detail="Cannot join your own session")

    # Check if user exists, create if not
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(id=request.user_id)
        db.add(user)
        await db.flush()  # Flush to get the user in the session

    # Update session with player 2 and change status to active
    session.player2_id = request.user_id
    session.status = "active"

    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        session_id=session.id,
        player1_id=session.player1_id,
        player2_id=session.player2_id,
        created_at=session.created_at,
        status=session.status,
        condition=session.condition,
        battle_video_url=session.battle_video_url,
        has_confrontation_image=bool(session.confrontation_image),
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get session details by ID.

    Args:
        session_id: The ID of the session to retrieve

    Returns:
        SessionResponse: The session details

    Raises:
        HTTPException: If session doesn't exist
    """
    # Get session
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.id,
        player1_id=session.player1_id,
        player2_id=session.player2_id,
        created_at=session.created_at,
        status=session.status,
        condition=session.condition,
        battle_video_url=session.battle_video_url,
        has_confrontation_image=bool(session.confrontation_image),
    )


@router.post("/start-round/{session_id}")
async def start_round(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Start a round for a session and notify all participants.

    Args:
        session_id: The ID of the session to start the round for

    Returns:
        dict: Success message

    Raises:
        HTTPException: If session doesn't exist or other errors occur
    """
    # Get session
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Add both users to the session for WebSocket messaging
    if session.player1_id:
        manager.add_to_session(session_id, session.player1_id)
    if session.player2_id:
        manager.add_to_session(session_id, session.player2_id)

    # Send round_start event to all users in the session
    await manager.send_session_message(
        {
            "type": "round_start",
            "session_id": session_id,
            "condition": session.condition,
        },
        session_id,
    )

    return {"message": "Round started", "session_id": session_id}
