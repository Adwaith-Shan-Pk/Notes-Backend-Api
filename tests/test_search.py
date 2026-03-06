import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_header(client):
    await client.post(
        "/api/auth/register",
        json={"email": "searcher@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "searcher@example.com", "password": "securepass123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def notes_for_search(client, auth_header):
    titles = ["Python tips", "FastAPI guide", "Python async tricks", "Docker basics"]
    for title in titles:
        await client.post(
            "/api/notes",
            json={"title": title, "content": "content here"},
            headers=auth_header,
        )


class TestSearch:
    async def test_search_by_title(self, client, auth_header, notes_for_search):
        resp = await client.get("/api/notes?search=python", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        titles = [n["title"] for n in data["data"]]
        assert all("python" in t.lower() for t in titles)

    async def test_search_case_insensitive(self, client, auth_header, notes_for_search):
        resp = await client.get("/api/notes?search=PYTHON", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    async def test_search_no_results(self, client, auth_header, notes_for_search):
        resp = await client.get("/api/notes?search=kubernetes", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_search_respects_ownership(self, client, notes_for_search):
        await client.post(
            "/api/auth/register",
            json={"email": "other2@example.com", "password": "securepass123"},
        )
        resp = await client.post(
            "/api/auth/login",
            json={"email": "other2@example.com", "password": "securepass123"},
        )
        other_header = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        resp = await client.get("/api/notes?search=python", headers=other_header)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0  

class TestSorting:
    async def test_sort_by_title_asc(self, client, auth_header, notes_for_search):
        resp = await client.get(
            "/api/notes?sort_by=title&order=asc", headers=auth_header
        )
        assert resp.status_code == 200
        titles = [n["title"] for n in resp.json()["data"]]
        assert titles == sorted(titles)

    async def test_sort_by_title_desc(self, client, auth_header, notes_for_search):
        resp = await client.get(
            "/api/notes?sort_by=title&order=desc", headers=auth_header
        )
        assert resp.status_code == 200
        titles = [n["title"] for n in resp.json()["data"]]
        assert titles == sorted(titles, reverse=True)

    async def test_invalid_sort_field_returns_400(self, client, auth_header):
        resp = await client.get("/api/notes?sort_by=invalid_field", headers=auth_header)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    async def test_invalid_order_returns_400(self, client, auth_header):
        resp = await client.get("/api/notes?order=sideways", headers=auth_header)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


class TestPagination:
    async def test_pagination_limit(self, client, auth_header, notes_for_search):
        resp = await client.get("/api/notes?page=1&limit=2", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["total"] == 4
        assert data["total_pages"] == 2

    async def test_pagination_page_2(self, client, auth_header, notes_for_search):
        resp = await client.get("/api/notes?page=2&limit=2", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    async def test_limit_over_100_fails(self, client, auth_header):
        resp = await client.get("/api/notes?limit=101", headers=auth_header)
        assert resp.status_code == 422

    async def test_search_with_pagination(self, client, auth_header, notes_for_search):
        resp = await client.get(
            "/api/notes?search=python&page=1&limit=1", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["total_pages"] == 2
        assert len(data["data"]) == 1
