from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import AppException
from app.config import settings


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
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


async def login_user(db: AsyncSession, data: LoginRequest) -> dict:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Same error for wrong email OR wrong password — enumeration prevention 
    if not user or not verify_password(data.password, user.password_hash):
        raise AppException(401, "INVALID_CREDENTIALS", "Invalid email or password")

    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })
    raw_refresh = create_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db_token = RefreshToken(
        token=raw_refresh,
        user_id=user.id,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise AppException(401, "TOKEN_INVALID", "Refresh token is invalid or expired")

    # Load associated user
    user_result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise AppException(401, "TOKEN_INVALID", "User no longer exists")

    # Issue new access token
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,  # reuse same refresh token
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }
