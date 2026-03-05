from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None


class NoteResponse(BaseModel):
    id: UUID
    title: str
    content: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedNotes(BaseModel):
    data: list[NoteResponse]
    total: int
    page: int
    total_pages: int
