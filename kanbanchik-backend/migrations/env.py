import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
# Импортируем асинхронную функцию для создания движка из конфига alembic.ini
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.db.base import Base

# Импортируем модели, чтобы они зарегистрировались в Base.metadata
from app.modules.users.models import User
from app.modules.boards.models import Board

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Эта вспомогательная функция запускает сами миграции внутри асинхронного соединения
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Используем async_engine_from_config вместо обычного engine_from_config
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Асинхронно подключаемся к базе данных через async with
    async with connectable.connect() as connection:
        # run_sync безопасно выполняет синхронную функцию do_run_migrations
        # внутри асинхронного контекста, передавая туда текущее соединение
        await connection.run_sync(do_run_migrations)

    # Закрываем пул соединений
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())