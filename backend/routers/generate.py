from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from models.database import Session, User, Character, get_db
from utils.image_generation import generate_character_image
import uuid
import base64

router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateCharacterRequest(BaseModel):
    prompt: str
    session_id: str
    user_id: str


class GenerateCharacterResponse(BaseModel):
    character_id: str
    session_id: str
    user_id: str
    prompt_used: str
    generated_at: datetime
    image_base64: str  # Base64 encoded image for easy frontend consumption

    class Config:
        from_attributes = True


@router.post("/", response_model=GenerateCharacterResponse)
async def generate_character(
    request: GenerateCharacterRequest, db: AsyncSession = Depends(get_db)
):
    """
    Generate a character image based on the prompt and store it in the database.

    Args:
        request: Contains prompt, session_id, and user_id

    Returns:
        GenerateCharacterResponse: The created character with image data
    """
    try:
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
        if (
            session.player1_id != request.user_id
            and session.player2_id != request.user_id
        ):
            raise HTTPException(
                status_code=403, detail="User is not part of this session"
            )

        # Generate character image
        try:
            image_data = generate_character_image(request.prompt)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to generate image: {str(e)}"
            )

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

        # Convert image to base64 for response
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        return GenerateCharacterResponse(
            character_id=new_character.id,
            session_id=new_character.session_id,
            user_id=new_character.user_id,
            prompt_used=new_character.prompt_used,
            generated_at=new_character.generated_at,
            image_base64=image_base64,
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to generate character: {str(e)}"
        )


@router.get("/{character_id}/image")
async def get_character_image(character_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the character image as binary data.

    Args:
        character_id: The ID of the character

    Returns:
        Raw image data with appropriate content type
    """
    try:
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve character image: {str(e)}"
        )
