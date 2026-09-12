from typing import Protocol
from datetime import datetime, timezone, timedelta

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.modules.auth.schemas import RefreshTokenData
from app.core.exceptions import InternalServerErrorException

# Константа для префикса ключей в Redis
REFRESH_TOKEN_KEY_PREFIX = "refresh_token:"


class IRefreshTokenRepository(Protocol):
    """Интерфейс репозитория для работы с refresh-токенами."""

    async def save(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        """Сохраняет токен с указанным TTL (в секундах)."""
        ...

    async def get(self, jti: str) -> RefreshTokenData | None:
        """Возвращает данные токена или None, если ключ не найден."""
        ...

    async def delete(self, jti: str) -> None:
        """Удаляет токен из Redis."""
        ...

    async def exists(self, jti: str) -> bool:
        """Проверяет, существует ли токен."""
        ...


class RedisRefreshTokenRepository:
    """Реализация репозитория на основе Redis."""

    def __init__(self, redis: Redis):
        self._redis = redis

    def _make_key(self, jti: str) -> str:
        return f"{REFRESH_TOKEN_KEY_PREFIX}{jti}"

    async def save(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        data = RefreshTokenData(
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
            created_at=datetime.now(timezone.utc),
        )
        key = self._make_key(jti)
        # Сохраняем как JSON-строку с TTL
        try:
            await self._redis.setex(key, ttl_seconds, data.model_dump_json())
        except RedisError:
            raise InternalServerErrorException("Ошибка при сохранении refresh-токена")

    async def get(self, jti: str) -> RefreshTokenData | None:
        key = self._make_key(jti)
        try:
            raw = await self._redis.get(key)
        except RedisError:
            raise InternalServerErrorException("Ошибка при получении refresh-токена")
        if raw is None:
            return None
        # Парсим JSON в Pydantic-модель
        return RefreshTokenData.model_validate_json(raw)

    async def delete(self, jti: str) -> None:
        key = self._make_key(jti)
        try:
            await self._redis.delete(key)
        except RedisError:
            raise InternalServerErrorException("Ошибка при удалении refresh-токена")

    async def exists(self, jti: str) -> bool:
        key = self._make_key(jti)
        try:
            return await self._redis.exists(key) == 1
        except RedisError:
            raise InternalServerErrorException("Ошибка при проверке refresh-токена")
