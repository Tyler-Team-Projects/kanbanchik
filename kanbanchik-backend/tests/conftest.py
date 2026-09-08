import pytest
import asyncio
from httpx import AsyncClient
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.fastapi import setup_dishka, FastapiProvider
from alembic.config import Config
from alembic import command

from app.core.config import settings, Settings
from app.main import app

from app.modules.auth.provider import AuthProvider
from app.modules.users.provider import UsersProvider
from app.modules.boards.provider import BoardsProvider
from app.modules.workspaces.provider import WorkspacesProvider
from app.modules.lists.provider import ListsProvider
from app.core.redis import RedisProvider

from app.api.deps import get_current_user
from app.api.schemas import CurrentUser
from uuid_extension import uuid7


@pytest.fixture(scope="session")
def event_loop():
    """Обязательно для session-scope асинхронных фикстур."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_test_database():
    """
    1. Проверяет/создает чистую тестовую БД.
    2. Запускает реальные миграции Alembic (гарантия корректности схемы).
    """
    sync_url = settings.TEST_DATABASE_URL.replace("+asyncpg", "")
    base_url, db_name = sync_url.rsplit("/", 1)

    import asyncpg
    conn = await asyncpg.connect(base_url + "/postgres")
    exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    if not exists:
        await conn.execute(f"CREATE DATABASE {db_name}")
    await conn.close()

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.TEST_DATABASE_URL)

    # Синхронный вызов alembic в отдельном потоке, так как alembic по умолчанию синхронен
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    yield

    await asyncio.to_thread(command.downgrade, alembic_cfg, "base")


# Специальный тестовый провайдер для Dishka
class TestDatabaseProvider(Provider):
    """
    Этот провайдер заменяет ваш оригинальный CoreProvider и DatabaseProvider в тестах.
    Он подменяет Engine на тестовый и изолирует каждую сессию в транзакции.
    """

    def __init__(self, test_database_url: str):
        super().__init__()
        # Создаем тестовый движок
        self.engine = create_async_engine(test_database_url, echo=False)

    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        return settings

    @provide(scope=Scope.APP)
    def get_engine(self) -> create_async_engine:
        return self.engine

    @provide(scope=Scope.REQUEST)
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        На каждый запрос/тест открывается соединение,
        запускается транзакция, а в конце — тотальный ROLLBACK.
        """
        async with self.engine.connect() as conn:
            trans = await conn.begin()

            async with AsyncSession(bind=conn, expire_on_commit=False) as session:
                yield session

            await trans.rollback()


@pytest.fixture(scope="function")
async def test_container(setup_test_database):
    """
    Пересобирает контейнер Dishka для каждого теста, гарантируя,
    что приложение FastAPI использует тестовый провайдер БД.
    """
    # Инициализируем наш тестовый провайдер с тестовым URL
    test_db_provider = TestDatabaseProvider(settings.TEST_DATABASE_URL)

    container = make_async_container(
        test_db_provider,
        RedisProvider(),
        FastapiProvider(),
        UsersProvider(),
        WorkspacesProvider(),
        AuthProvider(),
        BoardsProvider(),
        ListsProvider(),
    )

    # Намертво связываем этот контейнер с FastAPI приложением
    setup_dishka(container, app)

    yield container

    await container.close()
    # Закрываем пул соединений тестового движка
    await test_db_provider.engine.dispose()


@pytest.fixture(scope="function")
async def async_client(test_container):
    """
    Ваш клиент для выполнения HTTP-запросов к API.
    Зависит от test_container, поэтому БД гарантированно будет чистой.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


from app.api.deps import get_current_user
from app.api.schemas import CurrentUser
from uuid import uuid4


@pytest.fixture
def auth_client(async_client):
    """
    Возвращает клиент, который уже авторизован под фейковым пользователем.
    """
    fake_user = CurrentUser(
        id=uuid7(),
        email="test_user@kanbanchik.ru",
        username="test_user"
    )

    # Вот здесь FastAPI overrides уместен, так как get_current_user — это Depends
    app.dependency_overrides[get_current_user] = lambda: fake_user

    yield async_client

    app.dependency_overrides.clear()