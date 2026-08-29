from typing import Protocol
from uuid import UUID
from decimal import Decimal

from app.modules.lists.models import List
from app.modules.lists.schemas import ListCreate, ListUpdate
from app.modules.lists.repository import IListRepository


class IListService(Protocol):
    async def create(self, data: ListCreate) -> List: ...
    async def get_by_id(self, list_id: UUID) -> List | None: ...
    async def get_by_board(self, board_id: UUID, include_archived: bool = False) -> list[List]: ...
    async def get_active_by_board(self, board_id: UUID) -> list[List]: ...
    async def get_archived_by_board(self, board_id: UUID) -> list[List]: ...
    async def update(self, list_id: UUID, data: ListUpdate) -> List: ...
    async def move(self, list_id: UUID, new_position: Decimal) -> List: ...
    async def delete(self, list_id: UUID) -> None: ...


class ListService:
    def __init__(self, repo: IListRepository):
        self._repo = repo

    async def create(self, data: ListCreate) -> List:
        if data.position is None:
            position = await self._repo.get_next_position(data.board_id)
        else:
            position = data.position

        list = List(
            board_id=data.board_id,
            name=data.name,
            position=position,
            wip_limit=data.wip_limit,
        )
        return await self._repo.create(list)

    async def get_by_id(self, list_id: UUID) -> List | None:
        return await self._repo.get_by_id(list_id)

    async def get_by_board(self, board_id: UUID, include_archived: bool = False) -> list[List]:
        return await self._repo.get_by_board(board_id, include_archived)

    async def get_active_by_board(self, board_id: UUID) -> list[List]:
        return await self._repo.get_active_by_board(board_id)

    async def get_archived_by_board(self, board_id: UUID) -> list[List]:
        return await self._repo.get_archived_by_board(board_id)

    async def update(self, list_id: UUID, data: ListUpdate) -> List:
        """Обновить колонку с оптимистичной блокировкой."""

        # 1. Получаем текущую версию
        current = await self._repo.get_by_id(list_id)
        if not current:
            raise ValueError("Колонка не найдена")

        # 2. Собираем только изменённые поля
        fields = {}
        if data.name is not None and data.name != current.name:
            fields["name"] = data.name
        if data.position is not None and data.position != current.position:
            fields["position"] = data.position
        if data.wip_limit is not None and data.wip_limit != current.wip_limit:
            fields["wip_limit"] = data.wip_limit
        if data.is_archived is not None and data.is_archived != current.is_archived:
            fields["is_archived"] = data.is_archived

        # 3. Если ничего не изменилось - возвращаем текущий объект
        if not fields:
            return current

        # 4. Обновляем с проверкой версии
        return await self._repo.update_fields(list_id, fields, current.version)

    async def move(self, list_id: UUID, new_position: Decimal) -> List:
        current = await self._repo.get_by_id(list_id)
        if not current:
            raise ValueError("Колонка не найдена")

        if current.position == new_position:
            return current

        fields = {"position": new_position}
        return await self._repo.update_fields(list_id, fields, current.version)

    async def delete(self, list_id: UUID) -> None:
        list = await self._repo.get_by_id(list_id)
        if not list:
            raise ValueError("Колонка не найдена")
        await self._repo.delete(list_id)