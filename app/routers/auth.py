from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import RegisterRequest
from app.schemas.user import UserResponse
from app.services import auth_service
from app.dependencies import get_db

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, data)
    return user
