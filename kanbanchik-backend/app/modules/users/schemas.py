import re

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_-]+$')
    password: str = Field(min_length=8)
    name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[a-z]", value):
            raise ValueError("Пароль должен содержать как минимум 1 строчную букву")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Пароль должен содержать как минимум 1 заглавную букву")
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать как минимум 1 цифру")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValueError("Пароль должен содержать как минимум 1 специальный символ")
        return value


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)
    avatar_url: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    name: str | None
    bio: str | None
    avatar_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime



