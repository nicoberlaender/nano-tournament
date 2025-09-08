from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from models.database import Session, User, get_db
from utils.image_generation import generate_fight_condition
import uuid

router = APIRouter(prefix="/session", tags=["session"])


class CreateSessionRequest(BaseModel):
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
    try:
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

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create session: {str(e)}"
        )
