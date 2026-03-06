# Notes Management API

A fully functional REST API for managing personal notes, built with **FastAPI**, **Supabase (PostgreSQL)**, and **JWT authentication**. Supports user registration, login with refresh tokens, personal notes CRUD, pagination, search, and role-based admin access.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Docker Setup](#docker-setup)
- [Environment Variables](#environment-variables)
- [API Endpoint Reference](#api-endpoint-reference)
- [Example Requests](#example-requests)
- [Creating an Admin User](#creating-an-admin-user)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.12+
- A [Supabase](https://supabase.com) account (free tier works)
- pip / virtualenv
- Docker & Docker Compose (optional)

---

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Adwaith-Shan-Pk/Notes-Backend-Api.git
cd Notes-Backend-Api

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your Supabase credentials and a secret key

# 5. Run database migrations
alembic upgrade head

# 6. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API is now running at **http://localhost:8000**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Docker Setup

```bash
# 1. Copy and fill in .env
cp .env.example .env

# 2. Build and start
docker-compose up --build

# 3. Stop
docker-compose down
```

> The container automatically runs `alembic upgrade head` before starting uvicorn.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | `postgresql+asyncpg://user:pass@host/db` |
| `SECRET_KEY` | ✅ | — | JWT signing key (min 32 chars) |
| `ALGORITHM` | | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | | `7` | Refresh token lifetime |
| `APP_ENV` | | `development` | `development` or `production` |
| `APP_HOST` | | `0.0.0.0` | Server bind host |
| `APP_PORT` | | `8000` | Server bind port |

---

## API Endpoint Reference

### Authentication — `/api/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | None | Register a new user |
| POST | `/api/auth/login` | None | Login, receive access + refresh tokens |
| POST | `/api/auth/refresh` | None | Exchange refresh token for new access token |

### Notes — `/api/notes`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/notes` | JWT | List own notes (paginated, searchable) |
| POST | `/api/notes` | JWT | Create a new note |
| GET | `/api/notes/{id}` | JWT | Get a single note (must own it) |
| PUT | `/api/notes/{id}` | JWT | Partially update a note (must own it) |
| DELETE | `/api/notes/{id}` | JWT | Delete a note (must own it) |

**Query params for `GET /api/notes`:**

| Param | Default | Description |
|---|---|---|
| `page` | `1` | Page number |
| `limit` | `20` | Items per page (max 100) |
| `search` | — | Case-insensitive title search |
| `sort_by` | `created_at` | `created_at` \| `updated_at` \| `title` |
| `order` | `desc` | `asc` \| `desc` |

### Admin — `/api/admin` *(admin role required)*

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/admin/notes` | JWT (admin) | List ALL notes from all users |
| DELETE | `/api/admin/notes/{id}` | JWT (admin) | Delete any note |
| GET | `/api/admin/users` | JWT (admin) | List all users |

---

## Example Requests

### Register

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "mypassword123"}'
```

**Response (201):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "role": "user",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

---

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "mypassword123"}'
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dGhpcyBpcyBhIHJhbmRvbSB0b2tlbg...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### Create a Note

```bash
curl -X POST http://localhost:8000/api/notes \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Note", "content": "Hello, world!"}'
```

**Response (201):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "My First Note",
  "content": "Hello, world!",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2025-01-01T00:01:00Z",
  "updated_at": "2025-01-01T00:01:00Z"
}
```

---

### List Notes (with search & pagination)

```bash
curl "http://localhost:8000/api/notes?search=first&page=1&limit=10&sort_by=title&order=asc" \
  -H "Authorization: Bearer <access_token>"
```

**Response (200):**
```json
{
  "data": [...],
  "total": 1,
  "page": 1,
  "total_pages": 1
}
```

---

### Update a Note (partial)

```bash
curl -X PUT http://localhost:8000/api/notes/f47ac10b-58cc-4372-a567-0e02b2c3d479 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

---

### Delete a Note

```bash
curl -X DELETE http://localhost:8000/api/notes/f47ac10b-58cc-4372-a567-0e02b2c3d479 \
  -H "Authorization: Bearer <access_token>"
```

**Response: 204 No Content**

---

### Refresh Access Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

---

### Error Response Format

All errors use this consistent shape:

```json
{
  "error": {
    "code": "NOTE_NOT_FOUND",
    "message": "Note not found"
  }
}
```

| Code | Status | When |
|---|---|---|
| `TOKEN_MISSING` | 401 | No Authorization header |
| `TOKEN_INVALID` | 401 | Malformed or bad signature |
| `TOKEN_EXPIRED` | 401 | JWT past expiry |
| `INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `EMAIL_ALREADY_EXISTS` | 409 | Duplicate email on register |
| `NOTE_NOT_FOUND` | 404 | Note doesn't exist or not owned |
| `FORBIDDEN` | 403 | Non-admin hitting admin route |
| `VALIDATION_ERROR` | 422 | Invalid request body |

---

## Creating an Admin User

Admin role cannot be set through the API. To promote a user to admin:

1. Open your [Supabase Dashboard](https://app.supabase.com)
2. Navigate to **Table Editor → users**
3. Find the user's row
4. Set the `role` column to `admin`
5. Save

That user can now access all `/api/admin/*` endpoints.

---

## Troubleshooting

**`asyncpg` connection errors**
- Ensure `DATABASE_URL` uses `postgresql+asyncpg://` (not `postgresql://`)
- Check your Supabase project is active and the password is correct

**`alembic upgrade head` fails**
- Make sure `.env` is present and `DATABASE_URL` is set
- Run from the project root directory

**`TOKEN_INVALID` on valid token**
- Ensure `SECRET_KEY` in `.env` hasn't changed since the token was issued
- Check the token hasn't been corrupted (copy it without extra spaces)

**Port already in use**
- Change `APP_PORT` in `.env` or kill the process on port 8000

---

## Running Tests

```bash
pytest --cov=app --cov-report=term-missing -v
```
