from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, PaginatedNotes
from app.services import notes_service
from app.dependencies import get_db, get_current_user
from app.models.user import User

router = APIRouter()

_401 = {401: {"description": "TOKEN_MISSING | TOKEN_INVALID | TOKEN_EXPIRED"}}
_404 = {404: {"description": "NOTE_NOT_FOUND"}}
_422 = {422: {"description": "VALIDATION_ERROR"}}


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**_401, **_422},
    summary="Create a note",
)
async def create_note(
    data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new note for the authenticated user.

    - **title**: 1–255 characters
    - **content**: at least 1 character
    - `user_id` is set automatically from the JWT — cannot be overridden
    """
    return await notes_service.create_note(db, data, current_user.id)


@router.get(
    "",
    response_model=PaginatedNotes,
    responses={**_401, **_422},
    summary="List own notes",
)
async def list_notes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, description="Case-insensitive title search"),
    sort_by: str = Query("created_at", description="Sort field: created_at | updated_at | title"),
    order: str = Query("desc", description="Sort direction: asc | desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all notes belonging to the authenticated user with pagination and optional search.

    - **search**: filters by title using ILIKE (case-insensitive, partial match)
    - **sort_by**: one of `created_at`, `updated_at`, `title`
    - **order**: `asc` or `desc`
    - Results only include the current user's own notes
    """
    return await notes_service.list_notes(
        db, current_user.id, page, limit, search, sort_by, order
    )


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    responses={**_401, **_404},
    summary="Get a single note",
)
async def get_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single note by ID.

    - Returns 404 if the note does not exist **or** belongs to another user (ownership is not revealed)
    """
    return await notes_service.get_note_for_user(db, note_id, current_user.id)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    responses={**_401, **_404, **_422},
    summary="Update a note",
)
async def update_note(
    note_id: UUID,
    data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update a note. All fields are optional — only provided fields are updated.

    - Returns 404 if the note does not exist or belongs to another user
    """
    return await notes_service.update_note(db, note_id, data, current_user.id)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**_401, **_404},
    summary="Delete a note",
)
async def delete_note(
    note_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete a note.

    - Returns 204 No Content on success
    - Returns 404 if the note does not exist or belongs to another user
    """
    await notes_service.delete_note(db, note_id, current_user.id)
