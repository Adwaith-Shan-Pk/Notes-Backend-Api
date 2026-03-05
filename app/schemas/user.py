from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
