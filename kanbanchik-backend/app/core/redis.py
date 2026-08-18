from redis.asyncio import Redis

from app.core.config import settings

_redis_client: Redis | None = None


async def init_redis() -> Redis:
    """Инициализация Redis-клиента."""
    global _redis_client
    _redis_client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    await _redis_client.ping()
    return _redis_client


async def close_redis() -> None:
    """Закрытие Redis-клиента."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def get_redis() -> Redis:
    """Получить Redis-клиент."""
    if _redis_client is None:
        raise RuntimeError("Redis not initialized")
    return _redis_client