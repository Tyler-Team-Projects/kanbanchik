from typing import Any

from factory import Factory, Faker, LazyAttribute
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.modules.users.models import User
from app.core.security import get_password_hash


class BaseAsyncFactory(Factory):
    """Базовая фабрика для моделей SQLAlchemy с async-сессией."""

    class Meta:
        abstract = True
        # По умолчанию сессия не установлена — выставляется в фикстуре
        sqlalchemy_session: AsyncSession | None = None

    @classmethod
    async def _create(cls, model_class: type, *args: Any, **kwargs: Any) -> Any:
        """Асинхронная реализация создания: добавляем в сессию и делаем flush."""
        session = cls._meta.sqlalchemy_session
        if session is None:
            raise RuntimeError(
                f"Для {cls.__name__} не установлена сессия. "
                f"Установите {cls.__name__}._meta.sqlalchemy_session = session в фикстуре."
            )

        instance = model_class(*args, **kwargs)
        session.add(instance)
        # flush, а не commit — чтобы запись попала в текущую транзакцию теста и откатилась в конце теста
        await session.flush()
        return instance


class UserFactory(BaseAsyncFactory):
    class Meta:
        model = User

    id = LazyAttribute(lambda _: uuid7())
    email = Faker("email")
    username = Faker("user_name")
    password_hash = LazyAttribute(lambda _: get_password_hash("test_password"))
    name = Faker("name")
    is_active = True