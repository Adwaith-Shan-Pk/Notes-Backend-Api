import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def user_auth_header(client):
    await client.post(
        "/api/auth/register",
        json={"email": "regular@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "regular@example.com", "password": "securepass123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestAdminRoutesRequireAdmin:
    async def test_list_notes_as_user_returns_403(self, client, user_auth_header):
        resp = await client.get("/api/admin/notes", headers=user_auth_header)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    async def test_delete_note_as_user_returns_403(self, client, user_auth_header):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.delete(
            f"/api/admin/notes/{fake_id}", headers=user_auth_header
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    async def test_list_users_as_user_returns_403(self, client, user_auth_header):
        resp = await client.get("/api/admin/users", headers=user_auth_header)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    async def test_unauthenticated_returns_401(self, client):
        resp = await client.get("/api/admin/notes")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_MISSING"
