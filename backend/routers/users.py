from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from models.database import User, get_db

router = APIRouter(prefix="/users", tags=["users"])


class CreateUserRequest(BaseModel):
    name: str


class UserResponse(BaseModel):
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse)
async def create_user(request: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user with the provided name as the user ID.

    Args:
        request: Contains the name that will be used as the user ID

    Returns:
        UserResponse: The created user with ID and timestamp

    Raises:
        HTTPException: If user already exists or other errors occur
    """
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.id == request.name))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=400, detail="User with this name already exists"
            )

        # Create new user with name as ID
        new_user = User(id=request.name)

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
