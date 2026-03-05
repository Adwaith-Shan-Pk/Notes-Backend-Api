import math
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.note import Note
from app.schemas.note import NoteCreate
from app.core.exceptions import AppException


async def create_note(db: AsyncSession, data: NoteCreate, user_id: UUID) -> Note:
    note = Note(
        title=data.title,
        content=data.content,
        user_id=user_id,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def get_note_for_user(db: AsyncSession, note_id: UUID, user_id: UUID) -> Note:
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
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
) -> dict:
    offset = (page - 1) * limit

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(Note).where(Note.user_id == user_id)
    )
    total = count_result.scalar_one()

    # Fetch page
    result = await db.execute(
        select(Note)
        .where(Note.user_id == user_id)
        .order_by(Note.created_at.desc())
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
