import pytest
import pytest_asyncio
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

import app.database as db_module
from app.config import settings
from app.main import app


def _get_async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url



_test_engine = create_async_engine(
    _get_async_url(settings.database_url),
    poolclass=NullPool,
    echo=False,
)
_test_session_factory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)
db_module.engine = _test_engine
db_module.AsyncSessionLocal = _test_session_factory


@pytest_asyncio.fixture(scope="session")
async def client():
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client):
    creds = {"email": "e2e_user@example.com", "password": "securepass123"}
    resp = await client.post("/api/auth/register", json=creds)
    # Accept 201 (created) or 409 (already exists from a previous run)
    assert resp.status_code in (201, 409)
    return creds


@pytest_asyncio.fixture
async def user_tokens(client, registered_user):
    resp = await client.post("/api/auth/login", json=registered_user)
    assert resp.status_code == 200
    return resp.json()


@pytest_asyncio.fixture
async def user_headers(user_tokens):
    return {"Authorization": f"Bearer {user_tokens['access_token']}"}


@pytest_asyncio.fixture
async def second_user_headers(client):
    creds = {"email": "e2e_second@example.com", "password": "securepass123"}
    await client.post("/api/auth/register", json=creds)
    resp = await client.post("/api/auth/login", json=creds)
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
