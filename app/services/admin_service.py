import math
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.note import Note
from app.models.user import User
from app.core.exceptions import AppException


async def get_all_notes(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
) -> dict:
    offset = (page - 1) * limit

    count_result = await db.execute(select(func.count()).select_from(Note))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Note).order_by(Note.created_at.desc()).offset(offset).limit(limit)
    )
    notes = result.scalars().all()

    return {
        "data": notes,
        "total": total,
        "page": page,
        "total_pages": max(1, math.ceil(total / limit)),
    }


async def admin_delete_note(db: AsyncSession, note_id: UUID) -> None:
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise AppException(404, "NOTE_NOT_FOUND", "Note not found")
    await db.delete(note)
    await db.commit()


async def get_all_users(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
) -> dict:
    offset = (page - 1) * limit

    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar_one()

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    users = result.scalars().all()

    return {
        "data": users,
        "total": total,
        "page": page,
        "total_pages": max(1, math.ceil(total / limit)),
    }
