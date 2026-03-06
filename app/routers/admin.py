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

_401 = {401: {"description": "TOKEN_MISSING | TOKEN_INVALID | TOKEN_EXPIRED"}}
_403 = {403: {"description": "FORBIDDEN — admin role required"}}
_404 = {404: {"description": "NOTE_NOT_FOUND"}}


@router.get(
    "/notes",
    response_model=PaginatedNotes,
    responses={**_401, **_403},
    summary="[Admin] List all notes from all users",
)
async def list_all_notes(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, description="Case-insensitive title search across all users"),
    sort_by: str = Query("created_at", description="Sort field: created_at | updated_at | title"),
    order: str = Query("desc", description="Sort direction: asc | desc"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    **Admin only.** Return a paginated list of all notes from every user.

    - Supports the same search/sort/pagination params as `GET /api/notes`
    - Returns 403 if the caller does not have the `admin` role
    """
    return await admin_service.get_all_notes(db, page, limit, search, sort_by, order)


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**_401, **_403, **_404},
    summary="[Admin] Delete any note",
)
async def delete_any_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    **Admin only.** Permanently delete any note regardless of which user owns it.

    - Returns 204 on success
    - Returns 404 if the note does not exist
    - Returns 403 if the caller is not an admin
    """
    await admin_service.admin_delete_note(db, note_id)


@router.get(
    "/users",
    response_model=dict,
    responses={**_401, **_403},
    summary="[Admin] List all users",
)
async def list_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    **Admin only.** Return a paginated list of all registered users.

    - Password hashes are never included in the response
    - Returns 403 if the caller is not an admin
    """
    result = await admin_service.get_all_users(db, page, limit)
    result["data"] = [UserResponse.model_validate(u) for u in result["data"]]
    return result
