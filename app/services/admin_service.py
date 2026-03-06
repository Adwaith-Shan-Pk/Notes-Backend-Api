import math
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc

from app.models.note import Note
from app.models.user import User
from app.core.exceptions import AppException

ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "title"}


def _build_order(sort_by: str, order: str):
    col = getattr(Note, sort_by)
    return asc(col) if order == "asc" else desc(col)


async def get_all_notes(
    db: AsyncSession,
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
    filters = []
    if search:
        filters.append(Note.title.ilike(f"%{search}%"))

    count_result = await db.execute(
        select(func.count()).select_from(Note).where(*filters)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Note)
        .where(*filters)
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
