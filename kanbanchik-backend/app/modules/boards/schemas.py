from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BoardCreate(BaseModel):
    """Схема для создания доски."""
    workspace_id: UUID
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    background_color: str | None = Field(None, max_length=7)  # hex цвет
    background_image_url: str | None = Field(None, max_length=500)


class BoardUpdate(BaseModel):
    """Схема для обновления доски."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    background_color: str | None = Field(None, max_length=7)
    background_image_url: str | None = Field(None, max_length=500)
    is_archived: bool | None = None


class BoardResponse(BaseModel):
    """Схема для ответа API."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    background_color: str | None
    background_image_url: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime