from typing import Protocol
from uuid import UUID

from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.modules.users.repository import IUserRepository


class IUserService(Protocol):
    async def register(self, data: UserCreate) -> User: ...
    async def get_by_id(self, user_id: UUID) -> User | None: ...


class UserService:
    def __init__(self, repo: IUserRepository):
        self._repo = repo

    async def register(self, data: UserCreate) -> User:
        existing = await self._repo.get_by_email(str(data.email))
        if existing:
            raise ValueError("Email already registered")

        user = User(
            email=str(data.email),
            username=data.username,
            password_hash=data.password,  # позже: хеширование Argon2id
        )
        return await self._repo.create(user)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._repo.get_by_id(user_id)