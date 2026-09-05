from typing import Protocol
from uuid import UUID
from datetime import timedelta

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.repository import IRefreshTokenRepository
from app.modules.auth.schemas import RefreshTokenData
from app.modules.users.models import User
from app.modules.users.repository import IUserRepository
from uuid_extension import uuid7

from app.core.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    RefreshTokenNotFoundException,
    UserNotFoundException,
    UserInactiveException,
)


class IAuthService(Protocol):
    async def login(self, email: str, password: str) -> dict[str, str]:
        """Аутентификация пользователя, возвращает access и refresh токены."""
        ...

    async def refresh(self, refresh_token: str) -> dict[str, str]:
        """Обновляет пару токенов по refresh-токену (ротация)."""
        ...

    async def logout(self, refresh_token: str) -> None:
        """Инвалидирует refresh-токен (удаляет из Redis)."""
        ...

    async def get_user_from_token(self, token: str) -> User:
        """Декодирует токен, загружает и возвращает пользователя."""
        ...

class AuthService:
    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_repo: IRefreshTokenRepository,
        settings: Settings,
    ):
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo
        self._settings = settings

    async def login(self, email_or_username: str, password: str) -> tuple[str, str]:
        user = await self._user_repo.get_by_email_or_username(email_or_username)
        if not user:
            raise InvalidCredentialsException()
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()

        # Генерируем jti для refresh-токена
        jti = str(uuid7())
        # Время жизни refresh-токена в секундах
        refresh_ttl = self._settings.refresh_token_expire_days * 24 * 3600

        # Создаём payload для access и refresh
        access_payload = {"sub": str(user.id)}
        refresh_payload = {"sub": str(user.id), "jti": jti}

        access_token = create_access_token(
            data=access_payload,
            secret_key=self._settings.secret_key,
            expires_delta=timedelta(minutes=self._settings.access_token_expire_minutes),
            algorithm=self._settings.jwt_algorithm,
        )
        refresh_token = create_refresh_token(
            data=refresh_payload,
            secret_key=self._settings.secret_key,
            expires_delta=timedelta(days=self._settings.refresh_token_expire_days),
            algorithm=self._settings.jwt_algorithm,
        )

        # Сохраняем refresh-токен в Redis
        await self._refresh_repo.save(jti, str(user.id), refresh_ttl)

        return {"access_token": access_token, "refresh_token": refresh_token}

    async def refresh(self, refresh_token: str) -> dict[str, str]:
        # Декодируем refresh-токен
        try:
            payload = decode_token(refresh_token, self._settings.secret_key, self._settings.jwt_algorithm)
        except ValueError as e:
            raise InvalidTokenException()

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise InvalidTokenException()

        # Проверяем существование токена в Redis
        token_data = await self._refresh_repo.get(jti)
        if token_data is None:
            raise RefreshTokenNotFoundException()

        # Проверяем, что user_id совпадает с тем, что в токене
        if token_data.user_id != user_id:
            raise InvalidTokenException()

        # Удаляем старый refresh-токен (ротация)
        await self._refresh_repo.delete(jti)

        # Генерируем новую пару
        new_jti = str(uuid7())
        refresh_ttl = self._settings.refresh_token_expire_days * 24 * 3600

        access_payload = {"sub": user_id}
        refresh_payload = {"sub": user_id, "jti": new_jti}

        new_access = create_access_token(
            data=access_payload,
            secret_key=self._settings.secret_key,
            expires_delta=timedelta(minutes=self._settings.access_token_expire_minutes),
            algorithm=self._settings.jwt_algorithm,
        )
        new_refresh = create_refresh_token(
            data=refresh_payload,
            secret_key=self._settings.secret_key,
            expires_delta=timedelta(days=self._settings.refresh_token_expire_days),
            algorithm=self._settings.jwt_algorithm,
        )

        # Сохраняем новый refresh-токен
        await self._refresh_repo.save(new_jti, user_id, refresh_ttl)

        return {"access_token": new_access, "refresh_token": new_refresh}

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, self._settings.secret_key, self._settings.jwt_algorithm)
        except ValueError as e:
            raise InvalidTokenException()

        jti = payload.get("jti")
        if not jti:
            raise InvalidTokenException()

        # Удаляем из Redis
        await self._refresh_repo.delete(jti)

    async def get_user_from_token(self, token: str) -> User:
        """Декодирует токен, загружает и возвращает пользователя."""
        try:
            payload = decode_token(token, self._settings.secret_key, self._settings.jwt_algorithm)
        except ValueError as e:
            raise InvalidTokenException()

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenException()

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise InvalidTokenException()

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        if not user.is_active:
            raise UserInactiveException()

        return user