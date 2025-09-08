from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from models.database import Session, Character, Battle, get_db
from utils.llm_service import judge_battle
from utils.websocket_manager import manager
import uuid

router = APIRouter(prefix="/battle", tags=["battle"])


class BattleResultResponse(BaseModel):
    battle_id: str
    session_id: str
    winner_character_id: str
    winner_user_id: str
    battle_script: str
    battle_summary: str
    completed_at: datetime

    class Config:
        from_attributes = True


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
    try:
        # Get session
        session_result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if session is in battle state
        if session.status != "battle":
            raise HTTPException(
                status_code=400, detail="Session is not in battle state"
            )

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

        # Check if battle already exists for this session
        existing_battle_result = await db.execute(
            select(Battle).where(Battle.session_id == session_id)
        )
        existing_battle = existing_battle_result.scalar_one_or_none()

        if existing_battle:
            raise HTTPException(
                status_code=400, detail="Battle already resolved for this session"
            )

        # Use LLM judge to determine winner
        try:
            judge_result = judge_battle(
                player1_character_prompt=player1_character.prompt_used,
                player2_character_prompt=player2_character.prompt_used,
                battle_condition=session.condition or "Standard arena battle",
                player1_id=session.player1_id,
                player2_id=session.player2_id,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Battle judging failed: {str(e)}"
            )

        # Determine winner character
        winner_character = (
            player1_character
            if judge_result["winner_id"] == session.player1_id
            else player2_character
        )

        # Create battle record
        new_battle = Battle(
            id=str(uuid.uuid4()),
            session_id=session_id,
            player1_character_id=player1_character.id,
            player2_character_id=player2_character.id,
            winner_character_id=winner_character.id,
            battle_script=judge_result["battle_script"],
            battle_summary=judge_result["battle_summary"],
            completed_at=datetime.utcnow(),
        )

        # Update session status to completed
        session.status = "completed"

        # Save to database
        db.add(new_battle)
        await db.commit()
        await db.refresh(new_battle)
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
            battle_id=new_battle.id,
            session_id=new_battle.session_id,
            winner_character_id=new_battle.winner_character_id,
            winner_user_id=judge_result["winner_id"],
            battle_script=judge_result["battle_script"],
            battle_summary=judge_result["battle_summary"],
            completed_at=new_battle.completed_at,
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to resolve battle: {str(e)}"
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
        HTTPException: If session or battle doesn't exist
    """
    try:
        # Get battle
        battle_result = await db.execute(
            select(Battle).where(Battle.session_id == session_id)
        )
        battle = battle_result.scalar_one_or_none()

        if not battle:
            raise HTTPException(
                status_code=404, detail="Battle not found for this session"
            )

        # Get winner character to determine winner user
        winner_char_result = await db.execute(
            select(Character).where(Character.id == battle.winner_character_id)
        )
        winner_character = winner_char_result.scalar_one_or_none()

        if not winner_character:
            raise HTTPException(status_code=500, detail="Winner character not found")

        return BattleResultResponse(
            battle_id=battle.id,
            session_id=battle.session_id,
            winner_character_id=battle.winner_character_id,
            winner_user_id=winner_character.user_id,
            battle_script=battle.battle_script
            or "Two warriors engaged in an epic battle with spectacular moves and dramatic moments, culminating in a decisive victory.",
            battle_summary=battle.battle_summary or "Epic battle took place",
            completed_at=battle.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get battle result: {str(e)}"
        )
