from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lists.repository import IListRepository, ListRepository
from app.modules.lists.service import IListService, ListService


class ListsProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IListRepository)
    async def get_list_repo(self, session: AsyncSession) -> IListRepository:
        return ListRepository(session)

    @provide(scope=Scope.REQUEST, provides=IListService)
    async def get_list_service(self, repo: IListRepository) -> IListService:
        return ListService(repo)