from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.boards.repository import IBoardRepository, BoardRepository
from app.modules.boards.service import IBoardService, BoardService


class BoardsProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IBoardRepository)
    async def get_board_repo(self, session: AsyncSession) -> IBoardRepository:
        return BoardRepository(session)

    @provide(scope=Scope.REQUEST, provides=IBoardService)
    async def get_board_service(self, repo: IBoardRepository) -> IBoardService:
        return BoardService(repo)