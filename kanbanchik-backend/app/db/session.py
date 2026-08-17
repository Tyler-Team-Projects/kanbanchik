from sqlalchemy import text

from app.db.base import async_session_maker


async def check_db_connection() -> bool:
    """Проверка соединения с БД."""
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False