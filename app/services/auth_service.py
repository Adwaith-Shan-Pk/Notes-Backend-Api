from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.core.security import hash_password
from app.core.exceptions import AppException


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    # Check for duplicate email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise AppException(409, "EMAIL_ALREADY_EXISTS", "An account with this email already exists")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
