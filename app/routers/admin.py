from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.note import NoteResponse, PaginatedNotes
from app.schemas.user import UserResponse
from app.services import admin_service
from app.dependencies import get_db, require_admin
from app.models.user import User

router = APIRouter()


@router.get("/notes", response_model=PaginatedNotes)
async def list_all_notes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await admin_service.get_all_notes(db, page, limit, search, sort_by, order)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_any_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await admin_service.admin_delete_note(db, note_id)


@router.get("/users", response_model=dict)
async def list_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await admin_service.get_all_users(db, page, limit)
    result["data"] = [UserResponse.model_validate(u) for u in result["data"]]
    return result
