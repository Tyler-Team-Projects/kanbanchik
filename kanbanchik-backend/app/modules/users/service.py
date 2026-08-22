from typing import Protocol
from uuid import UUID
from argon2 import PasswordHasher

from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.modules.users.repository import IUserRepository

# Создаём экземпляр хешера (настройки по умолчанию – Argon2id)
_hasher = PasswordHasher()


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

        # Хешируем пароль с помощью Argon2id
        hashed = _hasher.hash(data.password)
        user = User(
            email=str(data.email),
            username=data.username,
            password_hash=hashed,
        )
        return await self._repo.create(user)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._repo.get_by_id(user_id)