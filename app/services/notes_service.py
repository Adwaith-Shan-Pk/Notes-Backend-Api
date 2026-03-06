import math
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate
from app.core.exceptions import AppException

ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "title"}


def _build_order(sort_by: str, order: str):
    col = getattr(Note, sort_by)
    return asc(col) if order == "asc" else desc(col)


async def create_note(db: AsyncSession, data: NoteCreate, user_id: UUID) -> Note:
    note = Note(title=data.title, content=data.content, user_id=UUID(str(user_id)))
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

async def get_note_for_user(db: AsyncSession, note_id: UUID, user_id: UUID) -> Note:
    result = await db.execute(
        select(Note).where(
            Note.id == UUID(str(note_id)),
            Note.user_id == UUID(str(user_id))
        )
    )
    note = result.scalar_one_or_none()
    if not note:
        raise AppException(404, "NOTE_NOT_FOUND", "Note not found")
    return note

async def list_notes(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
) -> dict:
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise AppException(400, "VALIDATION_ERROR", f"sort_by must be one of: {', '.join(ALLOWED_SORT_FIELDS)}")
    if order not in ("asc", "desc"):
        raise AppException(400, "VALIDATION_ERROR", "order must be 'asc' or 'desc'")

    offset = (page - 1) * limit
    base_filter = [Note.user_id == UUID(str(user_id))]

    if search:
        base_filter.append(Note.title.ilike(f"%{search}%"))

    count_result = await db.execute(
        select(func.count()).select_from(Note).where(*base_filter)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Note)
        .where(*base_filter)
        .order_by(_build_order(sort_by, order))
        .offset(offset)
        .limit(limit)
    )
    notes = result.scalars().all()

    return {
        "data": notes,
        "total": total,
        "page": page,
        "total_pages": max(1, math.ceil(total / limit)),
    }


async def update_note(
    db: AsyncSession, note_id: UUID, data: NoteUpdate, user_id: UUID
) -> Note:
    note = await get_note_for_user(db, note_id, user_id)
    if data.title is not None:
        note.title = data.title
    if data.content is not None:
        note.content = data.content
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(db: AsyncSession, note_id: UUID, user_id: UUID) -> None:
    note = await get_note_for_user(db, note_id, user_id)
    await db.delete(note)
    await db.commit()
