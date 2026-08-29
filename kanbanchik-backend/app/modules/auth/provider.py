from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from app.core.config import Settings
from app.modules.auth.repository import IRefreshTokenRepository, RedisRefreshTokenRepository
from app.modules.auth.service import AuthService, IAuthService
from app.modules.users.repository import IUserRepository


class AuthProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_refresh_token_repo(self, redis: Redis) -> IRefreshTokenRepository:
        return RedisRefreshTokenRepository(redis)

    @provide(scope=Scope.REQUEST, provides=IAuthService)
    async def get_auth_service(
        self,
        user_repo: IUserRepository,
        refresh_repo: IRefreshTokenRepository,
        settings: Settings,
    ) -> IAuthService:
        return AuthService(user_repo, refresh_repo, settings)
