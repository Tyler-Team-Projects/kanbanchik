from typing import Protocol
from uuid import UUID
from argon2 import PasswordHasher

from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate
from app.modules.users.repository import IUserRepository

from app.core.security import verify_password, get_password_hash


class IUserService(Protocol):
    async def register(self, data: UserCreate) -> User: ...
    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> User: ...
    async def get_by_id(self, user_id: UUID) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_username(self, username: str) -> User | None: ...
    async def update_profile(self, user_id: UUID, data: UserUpdate) -> User: ...
    async def deactivate(self, user_id: UUID) -> None: ...
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]: ...


class UserService:
    def __init__(self, repo: IUserRepository):
        self._repo = repo

    async def register(self, data: UserCreate) -> User:
        # Проверки уникальности
        existing_email = await self._repo.get_by_email(str(data.email))
        if existing_email:
            raise ValueError("Данная почта уже зарегистрирована")
        existing_username = await self._repo.get_by_username(data.username)
        if existing_username:
            raise ValueError("Данный username уже зарегистрирован")

        hashed = get_password_hash(data.password)
        user = User(
            email=str(data.email),
            username=data.username,
            password_hash=hashed,
            name=data.name,
            bio=data.bio,
        )
        return await self._repo.create(user)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._repo.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self._repo.get_by_email(email)

    async def get_by_username(self, username: str) -> User | None:
        return await self._repo.get_by_username(username)

    async def update_profile(self, user_id: UUID, data: UserUpdate) -> User:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        # Обновляем только переданные поля
        if data.email is not None:
            # Проверяем, что новый email не занят другим пользователем
            existing = await self._repo.get_by_email(str(data.email))
            if existing and existing.id != user_id:
                raise ValueError("Почта уже занята другим пользователем")
            user.email = str(data.email)
        if data.username is not None:
            existing = await self._repo.get_by_username(data.username)
            if existing and existing.id != user_id:
                raise ValueError("Username уже занят другим пользователем")
            user.username = data.username
        if data.name is not None:
            user.name = data.name
        if data.bio is not None:
            user.bio = data.bio
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url

        return await self._repo.update(user)

    async def deactivate(self, user_id: UUID) -> None:
        # Мягкое удаление (установка is_active=False)
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        user.is_active = False
        await self._repo.update(user)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        return await self._repo.get_all(skip, limit)

    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> User:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        if not verify_password(old_password, user.password_hash):
            raise ValueError("Неверный пароль")

        user.password_hash = get_password_hash(new_password)
        return await self._repo.update(user)