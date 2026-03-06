#Full Code Test
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _register_and_login(client, email: str, password: str = "securepass123"):
    await client.post("/api/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    data = resp.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }


class TestFullUserLifecycle:
    async def test_register_login_notes_crud(self, client):
        reg = await client.post(
            "/api/auth/register",
            json={"email": "lifecycle@example.com", "password": "securepass123"},
        )
        assert reg.status_code == 201
        assert reg.json()["role"] == "user"
        assert "password_hash" not in reg.json()

        login = await client.post(
            "/api/auth/login",
            json={"email": "lifecycle@example.com", "password": "securepass123"},
        )
        assert login.status_code == 200
        tokens = login.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        note1 = await client.post(
            "/api/notes",
            json={"title": "First Note", "content": "Hello world"},
            headers=headers,
        )
        assert note1.status_code == 201
        note_id = note1.json()["id"]
        assert note1.json()["title"] == "First Note"

        note2 = await client.post(
            "/api/notes",
            json={"title": "Second Note", "content": "More content"},
            headers=headers,
        )
        assert note2.status_code == 201

        list_resp = await client.get("/api/notes", headers=headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 2
        get_resp = await client.get(f"/api/notes/{note_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == note_id

        update_resp = await client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated First Note"},
            headers=headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "Updated First Note"
        assert update_resp.json()["content"] == "Hello world"  # unchanged

        delete_resp = await client.delete(f"/api/notes/{note_id}", headers=headers)
        assert delete_resp.status_code == 204

        verify = await client.get(f"/api/notes/{note_id}", headers=headers)
        assert verify.status_code == 404



class TestRefreshTokenFlow:
    async def test_refresh_gives_new_access_token(self, client):
        session = await _register_and_login(client, "refreshflow@example.com")

        refresh_resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": session["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != session["access_token"]

        new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        notes_resp = await client.get("/api/notes", headers=new_headers)
        assert notes_resp.status_code == 200

    async def test_invalid_refresh_token_rejected(self, client):
        resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "completely-bogus-token-xyz"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "TOKEN_INVALID"


class TestOwnershipEnforcement:
    async def test_user_cannot_access_other_users_note(self, client):
        user_a = await _register_and_login(client, "owner_a@example.com")
        user_b = await _register_and_login(client, "owner_b@example.com")
        note = await client.post(
            "/api/notes",
            json={"title": "A's secret", "content": "only mine"},
            headers=user_a["headers"],
        )
        note_id = note.json()["id"]

        assert (await client.get(f"/api/notes/{note_id}", headers=user_b["headers"])).status_code == 404
        assert (await client.put(f"/api/notes/{note_id}", json={"title": "hijacked"}, headers=user_b["headers"])).status_code == 404
        assert (await client.delete(f"/api/notes/{note_id}", headers=user_b["headers"])).status_code == 404

    async def test_search_scoped_to_owner(self, client):
        user_a = await _register_and_login(client, "search_owner@example.com")
        user_b = await _register_and_login(client, "search_other@example.com")

        await client.post("/api/notes", json={"title": "TopSecret", "content": "x"}, headers=user_a["headers"])

        resp = await client.get("/api/notes?search=TopSecret", headers=user_b["headers"])
        assert resp.json()["total"] == 0


class TestAdminCanDeleteAnyNote:
    async def test_regular_user_gets_403_on_admin_routes(self, client):
        user = await _register_and_login(client, "nonadmin@example.com")
        assert (await client.get("/api/admin/notes", headers=user["headers"])).status_code == 403
        assert (await client.get("/api/admin/users", headers=user["headers"])).status_code == 403
