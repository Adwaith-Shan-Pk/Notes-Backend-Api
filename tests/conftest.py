import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client):
    creds = {"email": "e2e_user@example.com", "password": "securepass123"}
    resp = await client.post("/api/auth/register", json=creds)
    assert resp.status_code == 201
    return {**creds, "id": resp.json()["id"]}


@pytest_asyncio.fixture
async def user_tokens(client, registered_user):
    resp = await client.post(
        "/api/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
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
