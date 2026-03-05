import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def registered_user(client):
    payload = {"email": "test@example.com", "password": "securepass123"}
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    return payload


@pytest.fixture
async def auth_tokens(client, registered_user):
    resp = await client.post("/api/auth/login", json=registered_user)
    assert resp.status_code == 200
    return resp.json()


class TestRegister:
    async def test_register_success(self, client):
        resp = await client.post(
            "/api/auth/register",
            json={"email": "newuser@example.com", "password": "password123"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert "password_hash" not in data

    async def test_register_duplicate_email(self, client, registered_user):
        resp = await client.post("/api/auth/register", json=registered_user)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"

    async def test_register_short_password(self, client):
        resp = await client.post(
            "/api/auth/register",
            json={"email": "short@example.com", "password": "abc"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client):
        resp = await client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client, registered_user):
        resp = await client.post("/api/auth/login", json=registered_user)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_login_wrong_password(self, client, registered_user):
        resp = await client.post(
            "/api/auth/login",
            json={"email": registered_user["email"], "password": "wrongpass"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_wrong_email(self, client):
        resp = await client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "password123"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


class TestRefresh:
    async def test_refresh_success(self, client, auth_tokens):
        resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_invalid_token(self, client):
        resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "totally-fake-token"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_INVALID"


class TestProtectedRoutes:
    async def test_missing_token_returns_401(self, client):
        resp = await client.get("/api/notes")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_MISSING"

    async def test_invalid_token_returns_401(self, client):
        resp = await client.get(
            "/api/notes",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_INVALID"
