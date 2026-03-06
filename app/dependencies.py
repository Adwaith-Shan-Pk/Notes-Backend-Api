from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import decode_access_token
from app.core.exceptions import AppException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise AppException(401, "TOKEN_MISSING", "Authorization token is required")

    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise AppException(401, "TOKEN_INVALID", "Token payload is malformed")

    try:
        user_uuid = UUID(user_id)
    except (ValueError, AttributeError):
        raise AppException(401, "TOKEN_INVALID", "Invalid user ID in token")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise AppException(401, "TOKEN_INVALID", "User no longer exists")

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise AppException(403, "FORBIDDEN", "Administrator access required")
    return current_user