import pytest
from contextvars import ContextVar
from typing import AsyncGenerator

from dotenv import load_dotenv
load_dotenv(".env.test", override=True)

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    AsyncConnection,
)
from redis.asyncio import Redis as AsyncRedis
from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.fastapi import FastapiProvider

from app.main import create_app
from app.modules.auth.provider import AuthProvider
from app.modules.users.provider import UsersProvider
from app.modules.boards.provider import BoardsProvider
from app.modules.workspaces.provider import WorkspacesProvider
from app.modules.lists.provider import ListsProvider
from app.core.config import Settings, settings
from app.api.deps import get_current_user
from app.api.schemas import CurrentUser

from tests.factories import UserFactory


_test_connection: ContextVar[AsyncConnection | None] = ContextVar(
    "_test_connection", default=None
)


class TestDatabaseProvider(Provider):
    """Подменяет боевой engine на тестовый и раздаёт session, привязанную к ContextVar."""

    def __init__(self, test_database_url: str):
        super().__init__()
        self.engine = create_async_engine(test_database_url, echo=False)

    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        return settings

    @provide(scope=Scope.APP)
    def get_engine(self) -> AsyncEngine:
        return self.engine

    @provide(scope=Scope.REQUEST)
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        conn = _test_connection.get()
        if conn is None:
            raise RuntimeError(
                "Тестовое соединение не установлено. "
                "Убедись, что тест зависит от фикстуры test_app (или db_transaction)."
            )
        session = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()


class TestRedisProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_redis(self) -> AsyncGenerator[AsyncRedis, None]:
        url = settings.test_redis_url or "redis://localhost:6380/0"
        client = AsyncRedis.from_url(url, decode_responses=True)
        try:
            yield client
        finally:
            await client.aclose()


@pytest.fixture(scope="session")
def test_db_provider():
    return TestDatabaseProvider(settings.test_database_url)


@pytest.fixture(scope="session")
async def test_container(test_db_provider):
    """
    Один контейнер на всю сессию.
    APP-scope ресурсы (engine, redis-клиент, Settings) создаются один раз.
    """
    container = make_async_container(
        test_db_provider,
        TestRedisProvider(),
        FastapiProvider(),
        UsersProvider(),
        WorkspacesProvider(),
        AuthProvider(),
        BoardsProvider(),
        ListsProvider(),
    )
    yield container
    await container.close()
    await test_db_provider.engine.dispose()


@pytest.fixture
async def db_transaction(test_db_provider):
    """
    Открывает соединение и BEGIN.
    Кладёт соединение в ContextVar, чтобы get_session внутри запросов
    использовал его же.
    В конце — ROLLBACK, всё стирается.
    """
    async with test_db_provider.engine.connect() as conn:
        trans = await conn.begin()
        token = _test_connection.set(conn)
        try:
            yield conn
        finally:
            _test_connection.reset(token)
            await trans.rollback()


@pytest.fixture
def test_app(test_container, db_transaction):
    """Свежий app на каждый тест. Зависит от db_transaction, чтобы ContextVar был установлен."""
    return create_app(test_container)


@pytest.fixture
async def async_client(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def auth_client(test_app, async_client, db_transaction, _clear_redis):
    session = AsyncSession(
        bind=db_transaction,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    UserFactory._session = session
    try:
        user = await UserFactory.create(
            email="test_user@kanbanchik.ru",
            username="test_user",
        )
        fake_user = CurrentUser(id=user.id, email=user.email, username=user.username)
        test_app.dependency_overrides[get_current_user] = lambda: fake_user
        yield async_client
        test_app.dependency_overrides.clear()
    finally:
        UserFactory._session = None
        await session.close()


@pytest.fixture()
async def _clear_redis(test_container):
    yield
    async with test_container() as req:
        redis = await req.get(AsyncRedis)
        await redis.flushdb()
