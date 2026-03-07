from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse
from app.services import auth_service
from app.dependencies import get_db
from app.core.limiter import limiter

router = APIRouter()

_401 = {401: {"description": "TOKEN_MISSING | TOKEN_INVALID | TOKEN_EXPIRED | INVALID_CREDENTIALS"}}
_409 = {409: {"description": "EMAIL_ALREADY_EXISTS"}}
_422 = {422: {"description": "VALIDATION_ERROR — invalid request body"}}
_429 = {429: {"description": "RATE_LIMIT_EXCEEDED"}}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**_409, **_422, **_429},
    summary="Register a new user",
)
@limiter.limit("10/minute")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={**_401, **_422, **_429},
    summary="Login and receive JWT tokens",
)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login_user(db, data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={**_401, **_422, **_429},
    summary="Refresh an access token",
)
@limiter.limit("20/minute")
async def refresh(request: Request, data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """token exchange"""
    return await auth_service.refresh_access_token(db, data.refresh_token)
