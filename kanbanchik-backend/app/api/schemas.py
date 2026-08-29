from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class CurrentUser(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime