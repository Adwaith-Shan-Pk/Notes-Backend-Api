from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse
from app.services import auth_service
from app.dependencies import get_db

router = APIRouter()

_401 = {401: {"description": "TOKEN_MISSING | TOKEN_INVALID | TOKEN_EXPIRED | INVALID_CREDENTIALS"}}
_409 = {409: {"description": "EMAIL_ALREADY_EXISTS"}}
_422 = {422: {"description": "VALIDATION_ERROR — invalid request body"}}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**_409, **_422},
    summary="Register a new user",
)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={**_401, **_422},
    summary="Login and receive JWT tokens",
)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    - Returns an access token(15 min) and a refresh token(7 days)
    - The same error is returned for wrong email or wrong password to prevent user enumeration
    """
    return await auth_service.login_user(db, data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={**_401, **_422},
    summary="Refresh an access token",
)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """token exchange"""
    return await auth_service.refresh_access_token(db, data.refresh_token)
