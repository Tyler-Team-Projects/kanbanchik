from dishka import Provider, Scope, provide, make_async_container
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from typing import AsyncIterable

from app.db.base import engine
from app.core.config import settings, Settings
from app.modules.users.provider import UsersProvider
from app.modules.boards.provider import BoardsProvider
from app.modules.workspaces.provider import WorkspacesProvider
from app.modules.lists.provider import ListsProvider


class CoreProvider(Provider):
    """App-scope: то, что живет во время работы сервера"""

    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        return settings

    @provide(scope=Scope.APP)
    def get_engine(self) -> AsyncEngine:
        return engine


class DatabaseProvider(Provider):
    """REQUEST-scope: новая сессия БД на каждый HTTP-запрос"""
    @provide(scope=Scope.APP)
    def get_session_maker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    @provide(scope=Scope.REQUEST)
    async def get_session(self, session_maker: async_sessionmaker[AsyncSession]) -> AsyncIterable[AsyncSession]:
        async with session_maker() as session:
            yield session


# Собираем ВСЕ провайдеры в один контейнер
container = make_async_container(
    CoreProvider(),
    DatabaseProvider(),
    UsersProvider(),
    BoardsProvider(),
    WorkspacesProvider(),
    ListsProvider(),
)