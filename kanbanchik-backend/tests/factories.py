from uuid_extension import uuid7
from factory import Factory, Faker, LazyAttribute
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.models import User
from app.core.security import get_password_hash


class UserFactory(Factory):
    class Meta:
        model = User

    id = LazyAttribute(lambda _: uuid7())
    email = Faker("email")
    username = Faker("user_name")
    password_hash = LazyAttribute(lambda _: get_password_hash("test_password"))
    is_active = True

    @classmethod
    async def create_in_db(cls, session: AsyncSession, **kwargs) -> User:
        """
        Создает объект и сразу сохраняет его в реальную тестовую БД.
        Использовать только в интеграционных тестах!
        """
        # Генерируем объект со всеми Faker-полями
        obj = cls.build(**kwargs)

        # Сохраняем в сессию
        session.add(obj)
        await session.flush()  # flush вместо commit, так как мы внутри тестовой транзакции
        return obj