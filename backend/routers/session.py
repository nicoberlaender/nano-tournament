from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from models.database import Session, User, Character, get_db
from utils.image_generation import generate_fight_condition
from utils.llm_service import judge_battle
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

    class Config:
        from_attributes = True


class BattleResultResponse(BaseModel):
    session_id: str
    winner_user_id: str
    battle_script: str
    battle_summary: str
    completed_at: datetime

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


@router.post("/resolve/{session_id}", response_model=BattleResultResponse)
async def resolve_battle(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Resolve a battle using LLM judge to determine the winner.

    Args:
        session_id: The ID of the session to resolve the battle for

    Returns:
        BattleResultResponse: The battle result with winner and reasoning

    Raises:
        HTTPException: If session doesn't exist, is not in battle state, or other errors occur
    """
    # Get session
    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if session is in active state (ready for battle)
    if session.status not in ["active", "battle"]:
        raise HTTPException(status_code=400, detail="Session is not ready for battle")

    if not session.player2_id:
        raise HTTPException(
            status_code=400, detail="Session needs 2 players for battle"
        )

    # Get characters for both players
    player1_char_result = await db.execute(
        select(Character)
        .where(
            Character.session_id == session_id,
            Character.user_id == session.player1_id,
        )
        .order_by(Character.generated_at.desc())
        .limit(1)
    )
    player1_character = player1_char_result.scalar_one_or_none()

    player2_char_result = await db.execute(
        select(Character)
        .where(
            Character.session_id == session_id,
            Character.user_id == session.player2_id,
        )
        .order_by(Character.generated_at.desc())
        .limit(1)
    )
    player2_character = player2_char_result.scalar_one_or_none()

    if not player1_character:
        raise HTTPException(status_code=400, detail="Player 1 has no character")

    if not player2_character:
        raise HTTPException(status_code=400, detail="Player 2 has no character")

    # Check if battle already resolved for this session
    if session.winner_user_id is not None:
        raise HTTPException(
            status_code=400, detail="Battle already resolved for this session"
        )

    # Update session status to battle
    session.status = "battle"

    # Use LLM judge to determine winner
    judge_result = judge_battle(
        player1_character_prompt=player1_character.prompt_used,
        player2_character_prompt=player2_character.prompt_used,
        battle_condition=session.condition or "Standard arena battle",
        player1_id=session.player1_id,
        player2_id=session.player2_id,
    )

    # Update session with battle results
    session.winner_user_id = judge_result["winner_id"]
    session.battle_script = judge_result["battle_script"]
    session.battle_summary = judge_result["battle_summary"]
    session.completed_at = datetime.utcnow()
    session.status = "completed"

    # Save to database
    await db.commit()
    await db.refresh(session)

    # Send results event to all users in the session
    await manager.send_session_message(
        {
            "type": "results",
            "session_id": session_id,
            "winner_user_id": judge_result["winner_id"],
            "battle_script": judge_result["battle_script"],
            "battle_summary": judge_result["battle_summary"],
        },
        session_id,
    )

    return BattleResultResponse(
        session_id=session.id,
        winner_user_id=session.winner_user_id,
        battle_script=session.battle_script,
        battle_summary=session.battle_summary,
        completed_at=session.completed_at,
    )


@router.get("/result/{session_id}", response_model=BattleResultResponse)
async def get_battle_result(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the battle result for a session.

    Args:
        session_id: The ID of the session to get the battle result for

    Returns:
        BattleResultResponse: The battle result

    Raises:
        HTTPException: If session doesn't exist or battle not completed
    """
    # Get session
    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.winner_user_id or not session.completed_at:
        raise HTTPException(
            status_code=404, detail="Battle not completed for this session"
        )

    return BattleResultResponse(
        session_id=session.id,
        winner_user_id=session.winner_user_id,
        battle_script=session.battle_script
        or "Two warriors engaged in an epic battle with spectacular moves and dramatic moments, culminating in a decisive victory.",
        battle_summary=session.battle_summary or "Epic battle took place",
        completed_at=session.completed_at,
    )
