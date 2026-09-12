from typing import AsyncIterable

from redis.asyncio import Redis
from dishka import Provider, Scope, provide

from app.core.config import settings


class RedisProvider(Provider):
    """DI-провайдер для redis-клиента."""

    @provide(scope=Scope.APP)
    async def get_redis(self) -> AsyncIterable[Redis]:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await client.ping()
            yield client
        finally:
            await client.aclose()