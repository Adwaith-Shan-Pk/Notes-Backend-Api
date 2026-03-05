from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.exceptions import AppException, app_exception_handler
from app.database import AsyncSessionLocal
from app.routers import auth, notes, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    yield


app = FastAPI(
    title="Notes Management API",
    description="A REST API for managing personal notes with JWT auth and RBAC",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

#health check 
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
