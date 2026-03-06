import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.database import AsyncSessionLocal
from app.routers import auth, notes, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    yield


app = FastAPI(
    title="Notes Management API",
    description=(
        "A fully functional REST API for managing personal notes.\n\n"
        "## Features\n"
        "- **JWT Authentication** — register, login, refresh tokens\n"
        "- **Personal Notes CRUD** — create, read, update, delete with ownership enforcement\n"
        "- **Search & Pagination** — case-insensitive title search, sort, paginate\n"
        "- **Role-Based Access Control** — admin endpoints for managing all notes and users\n\n"
        "## Authentication\n"
        "Use `POST /api/auth/login` to obtain a Bearer token, then click **Authorize** above."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "Register, login, and refresh JWT tokens"},
        {"name": "Notes", "description": "Create and manage your personal notes"},
        {"name": "Admin", "description": "Admin-only endpoints — requires `admin` role"},
        {"name": "Health", "description": "Service health check"},
    ],
)


# ── X-Request-ID middleware ───────────────────────────────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Request body size limit (1 MB) ───────────────────────────────────────────
@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    max_size = 1 * 1024 * 1024  # 1 MB
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=413,
            content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds the 1 MB limit"}},
        )
    return await call_next(request)


# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


#health check
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
