from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class RefreshTokenData(BaseModel):
    """Данные сохраняемые в Redis для refresh-токенов"""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    expires_at: datetime
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str