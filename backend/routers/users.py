from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from models.database import User, get_db

router = APIRouter(prefix="/users", tags=["users"])


class CreateUserRequest(BaseModel):
    user_id: str
    name: str


class UserResponse(BaseModel):
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse)
async def create_user(request: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user with the provided user_id (name is stored as user_id for now).

    Args:
        request: Contains the user_id and name

    Returns:
        UserResponse: The created user with ID and timestamp

    Raises:
        HTTPException: If user already exists or other errors occur
    """
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.id == request.user_id))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            return UserResponse(
                user_id=existing_user.id,
                created_at=existing_user.created_at,
            )

        # Create new user (user_id acts as name for now)
        new_user = User(id=request.user_id)

        # Add to database
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return UserResponse(
            user_id=new_user.id,
            created_at=new_user.created_at,
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
