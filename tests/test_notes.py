import pytest
from app.main import app

pytestmark = pytest.mark.asyncio



@pytest.fixture
async def auth_header(client):
    await client.post(
        "/api/auth/register",
        json={"email": "noter@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "noter@example.com", "password": "securepass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def other_auth_header(client):
    await client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "other@example.com", "password": "securepass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def created_note(client, auth_header):
    resp = await client.post(
        "/api/notes",
        json={"title": "My Note", "content": "Some content here"},
        headers=auth_header,
    )
    assert resp.status_code == 201
    return resp.json()


class TestCreateNote:
    async def test_create_success(self, client, auth_header):
        resp = await client.post(
            "/api/notes",
            json={"title": "Hello", "content": "World"},
            headers=auth_header,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Hello"
        assert data["content"] == "World"
        assert "user_id" in data
        assert "id" in data

    async def test_create_requires_auth(self, client):
        resp = await client.post("/api/notes", json={"title": "x", "content": "y"})
        assert resp.status_code == 401

    async def test_create_empty_title_fails(self, client, auth_header):
        resp = await client.post(
            "/api/notes",
            json={"title": "", "content": "content"},
            headers=auth_header,
        )
        assert resp.status_code == 422


class TestListNotes:
    async def test_list_empty(self, client, auth_header):
        resp = await client.get("/api/notes", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["data"] == []
        assert data["page"] == 1

    async def test_list_with_notes(self, client, auth_header, created_note):
        resp = await client.get("/api/notes", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_pagination_params(self, client, auth_header):
        resp = await client.get("/api/notes?page=1&limit=5", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["page"] == 1


class TestGetNote:
    async def test_get_own_note(self, client, auth_header, created_note):
        resp = await client.get(f"/api/notes/{created_note['id']}", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["id"] == created_note["id"]

    async def test_get_other_users_note_returns_404(
        self, client, created_note, other_auth_header
    ):
        resp = await client.get(
            f"/api/notes/{created_note['id']}", headers=other_auth_header
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOTE_NOT_FOUND"

    async def test_get_nonexistent_note(self, client, auth_header):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/notes/{fake_id}", headers=auth_header)
        assert resp.status_code == 404


class TestUpdateNote:
    async def test_update_title(self, client, auth_header, created_note):
        resp = await client.put(
            f"/api/notes/{created_note['id']}",
            json={"title": "Updated Title"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"
        assert resp.json()["content"] == created_note["content"]  # unchanged

    async def test_update_content_only(self, client, auth_header, created_note):
        resp = await client.put(
            f"/api/notes/{created_note['id']}",
            json={"content": "New content"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "New content"
        assert resp.json()["title"] == created_note["title"]  # unchanged

    async def test_update_other_users_note_returns_404(
        self, client, created_note, other_auth_header
    ):
        resp = await client.put(
            f"/api/notes/{created_note['id']}",
            json={"title": "Hack"},
            headers=other_auth_header,
        )
        assert resp.status_code == 404


class TestDeleteNote:
    async def test_delete_own_note(self, client, auth_header, created_note):
        resp = await client.delete(
            f"/api/notes/{created_note['id']}", headers=auth_header
        )
        assert resp.status_code == 204

        # Verify 
        get_resp = await client.get(
            f"/api/notes/{created_note['id']}", headers=auth_header
        )
        assert get_resp.status_code == 404

    async def test_delete_other_users_note_returns_404(
        self, client, created_note, other_auth_header
    ):
        resp = await client.delete(
            f"/api/notes/{created_note['id']}", headers=other_auth_header
        )
        assert resp.status_code == 404
