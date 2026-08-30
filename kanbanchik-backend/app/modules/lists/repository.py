from typing import Protocol
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, func, delete, update, bindparam
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lists.models import List


class IListRepository(Protocol):
    async def get_by_id(self, list_id: UUID) -> List | None: ...
    async def get_by_board(self, board_id: UUID, include_archived: bool = False) -> list[List]: ...
    async def get_active_by_board(self, board_id: UUID) -> list[List]: ...
    async def get_archived_by_board(self, board_id: UUID) -> list[List]: ...
    async def create(self, list: List) -> List: ...
    async def update(self, list: List) -> List: ...
    async def update_fields(self, list_id: UUID, fields: dict, version: int) -> List: ...
    async def delete(self, list_id: UUID) -> None: ...
    async def get_next_position(self, board_id: UUID) -> Decimal: ...
    async def update_positions(self, board_id: UUID, updates: list[dict]) -> None: ...


class ListRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, list_id: UUID) -> List | None:
        result = await self._session.execute(
            select(List).where(List.id == list_id)
        )
        return result.scalar_one_or_none()

    async def get_by_board(self, board_id: UUID, include_archived: bool = False) -> list[List]:
        """Получить все колонки доски с сортировкой по position."""
        query = select(List).where(List.board_id == board_id)
        if not include_archived:
            query = query.where(List.is_archived == False)
        query = query.order_by(List.position)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_active_by_board(self, board_id: UUID) -> list[List]:
        """Получить все активные колонки доски (is_archived=False)."""
        query = select(List).where(
            List.board_id == board_id,
            List.is_archived == False
        ).order_by(List.position)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_archived_by_board(self, board_id: UUID) -> list[List]:
        """Получить все архивные колонки доски (is_archived=True)."""
        query = select(List).where(
            List.board_id == board_id,
            List.is_archived == True
        ).order_by(List.position)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def create(self, list: List) -> List:
        self._session.add(list)
        await self._session.commit()
        await self._session.refresh(list)
        return list

    # TODO: удалить позже
    async def update(self, list: List) -> List:
        await self._session.commit()
        await self._session.refresh(list)
        return list

    async def update_fields(self, list_id: UUID, fields: dict, version: int) -> List:
        """Частичное обновление с оптимистичной блокировкой."""
        stmt = (
            update(List)
            .where(List.id == list_id, List.version == version)
            .values(**fields, version=List.version + 1)
            .returning(List)
        )
        result = await self._session.execute(stmt)
        updated = result.scalar_one_or_none()

        if updated is None:
            raise ValueError(
                "Конфликт обновления: запись была изменена другим пользователем. "
                "Пожалуйста, обновите страницу и попробуйте снова."
            )

        await self._session.commit()
        return updated

    async def delete(self, list_id: UUID) -> None:
        await self._session.execute(
            delete(List).where(List.id == list_id)
        )
        await self._session.commit()

    async def get_next_position(self, board_id: UUID) -> Decimal:
        """Получить следующую позицию для новой колонки."""
        result = await self._session.execute(
            select(func.max(List.position))
            .where(List.board_id == board_id)
        )
        max_position = result.scalar()
        if max_position is None:
            return Decimal('1.0')
        return max_position + Decimal('1.0')

    async def update_positions(self, board_id: UUID, updates: list[dict]) -> None:
        """Пакетное обновление позиций колонок."""

        # Проверяем, что все колонки принадлежат этой доске
        list_ids = [u["id"] for u in updates]
        result = await self._session.execute(
            select(List.id).where(
                List.board_id == board_id,
                List.id.in_(list_ids)
            )
        )
        existing_ids = set(result.scalars().all())

        if len(existing_ids) != len(list_ids):
            missing = set(list_ids) - existing_ids
            raise ValueError(f"Колонки с ID {missing} не найдены на доске {board_id}")

        def _bulk_update(connection):
            for u in updates:
                connection.execute(
                    update(List)
                    .where(List.id == u["id"])
                    .values(position=u["position"], updated_at=func.now())
                )

        await self._session.run_sync(_bulk_update)
        await self._session.commit()