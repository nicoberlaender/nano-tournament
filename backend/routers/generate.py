from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from models.database import Session, User, Character, get_db
from utils.image_generation import generate_character_image
from utils.llm_service import judge_battle
from utils.websocket_manager import manager
import uuid

router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateCharacterRequest(BaseModel):
    prompt: str
    session_id: str
    user_id: str


@router.post("/")
async def generate_character(
    request: GenerateCharacterRequest, db: AsyncSession = Depends(get_db)
):
    """
    Generate a character image based on the prompt and store it in the database.

    Args:
        request: Contains prompt, session_id, and user_id

    Returns:
        Raw image data with appropriate content type
    """
    # Validate session exists
    session_result = await db.execute(
        select(Session).where(Session.id == request.session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate user exists
    user_result = await db.execute(select(User).where(User.id == request.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate user is part of the session
    if session.player1_id != request.user_id and session.player2_id != request.user_id:
        raise HTTPException(status_code=403, detail="User is not part of this session")

    # Check if user already has a character in this session
    existing_char_result = await db.execute(
        select(Character).where(
            Character.session_id == request.session_id,
            Character.user_id == request.user_id,
        )
    )
    existing_character = existing_char_result.scalar_one_or_none()

    if existing_character:
        raise HTTPException(
            status_code=400,
            detail="Player already has a character in this session. Only one character per player is allowed.",
        )

    # Generate character image
    image_data = generate_character_image(request.prompt)

    # Create character record
    new_character = Character(
        id=str(uuid.uuid4()),
        session_id=request.session_id,
        user_id=request.user_id,
        image_data=image_data,
        prompt_used=request.prompt,
    )

    # Add to database
    db.add(new_character)
    await db.commit()
    await db.refresh(new_character)

    # Check if both players now have characters and auto-start battle
    await _check_and_start_battle_if_ready(db, session)

    # Return image as binary response
    return Response(content=image_data, media_type="image/png")  # Assuming PNG format


@router.get("/{character_id}/image")
async def get_character_image(character_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the character image as binary data.

    Args:
        character_id: The ID of the character

    Returns:
        Raw image data with appropriate content type
    """
    # Get character
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if not character.image_data:
        raise HTTPException(status_code=404, detail="Character image not found")

    # Return image as binary response
    return Response(
        content=character.image_data, media_type="image/png"  # Assuming PNG format
    )


async def _check_and_start_battle_if_ready(db: AsyncSession, session: Session):
    """
    Check if both players have created characters and automatically resolve the battle.

    Args:
        db: Database session
        session: The game session to check
    """
    # Only proceed if session is active (has 2 players) and not already resolved
    if session.status != "active" or not session.player2_id or session.winner_user_id:
        return

    # Check if both players have created their characters (exactly one each)
    player1_char_result = await db.execute(
        select(Character).where(
            Character.session_id == session.id,
            Character.user_id == session.player1_id,
        )
    )
    player1_character = player1_char_result.scalar_one_or_none()

    player2_char_result = await db.execute(
        select(Character).where(
            Character.session_id == session.id,
            Character.user_id == session.player2_id,
        )
    )
    player2_character = player2_char_result.scalar_one_or_none()

    # If both players have created their character, resolve the battle automatically
    if player1_character and player2_character:
        # Update session status to battle
        session.status = "battle"
        await db.commit()
        await db.refresh(session)

        # Add both users to the session for WebSocket messaging if not already added
        manager.add_to_session(session.id, session.player1_id)
        manager.add_to_session(session.id, session.player2_id)

        # Send battle_start event to both players
        await manager.send_session_message(
            {
                "type": "battle_start",
                "session_id": session.id,
            },
            session.id,
        )

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
                "session_id": session.id,
                "winner_user_id": judge_result["winner_id"],
                "battle_script": judge_result["battle_script"],
                "battle_summary": judge_result["battle_summary"],
            },
            session.id,
        )
