from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.repository import IUserRepository, UserRepository
from app.modules.users.service import IUserService, UserService


class UsersProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IUserRepository)
    async def get_user_repo(self, session: AsyncSession) -> IUserRepository:
        return UserRepository(session)

    @provide(scope=Scope.REQUEST, provides=IUserService)
    async def get_user_service(self, repo: IUserRepository) -> IUserService:
        return UserService(repo)