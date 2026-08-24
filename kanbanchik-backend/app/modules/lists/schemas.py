from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ListCreate(BaseModel):
    """Схема для создания колонки."""
    board_id: UUID
    name: str = Field(min_length=1, max_length=100)
    position: Decimal | None = Field(None, description="Позиция для сортировки (опционально)")
    wip_limit: int | None = Field(None, ge=1, description="Лимит карточек в колонке")


class ListUpdate(BaseModel):
    """Схема для обновления колонки."""
    name: str | None = Field(None, min_length=1, max_length=100)
    position: Decimal | None = Field(None, description="Новая позиция для сортировки")
    wip_limit: int | None = Field(None, ge=1)
    is_archived: bool | None = None


class ListResponse(BaseModel):
    """Схема для ответа API."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    board_id: UUID
    name: str
    position: Decimal
    wip_limit: int | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ListMove(BaseModel):
    """Схема для перемещения колонки (DnD)."""
    new_position: Decimal = Field(..., description="Новая позиция для сортировки")