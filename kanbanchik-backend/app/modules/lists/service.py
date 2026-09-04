from typing import Protocol
from uuid import UUID
from decimal import Decimal

from app.modules.lists.models import List
from app.modules.lists.schemas import ListCreate, ListUpdate
from app.modules.lists.repository import IListRepository


class IListService(Protocol):
    async def create(self, data: ListCreate, current_user_id: UUID) -> List: ...
    async def get_by_id(self, list_id: UUID, current_user_id: UUID) -> List | None: ...
    async def get_by_board(self, board_id: UUID, current_user_id: UUID, include_archived: bool = False) -> list[List]: ...
    async def get_active_by_board(self, board_id: UUID, current_user_id: UUID) -> list[List]: ...
    async def get_archived_by_board(self, board_id: UUID, current_user_id: UUID) -> list[List]: ...
    async def update(self, list_id: UUID, data: ListUpdate, current_user_id: UUID) -> List: ...
    async def reorder(self, board_id: UUID, list_ids: list[UUID], current_user_id: UUID) -> list[List]: ...
    async def delete(self, list_id: UUID, current_user_id: UUID) -> None: ...


class ListService:
    def __init__(self, repo: IListRepository):
        self._repo = repo

    async def create(self, data: ListCreate, current_user_id: UUID) -> List:
        # TODO: добавить проверку прав (доступ к доске)
        if data.position is None:
            position = await self._repo.get_next_position(data.board_id)
        else:
            position = data.position

        list_obj = List(
            board_id=data.board_id,
            name=data.name,
            position=position,
            wip_limit=data.wip_limit,
        )
        return await self._repo.create(list_obj)

    async def get_by_id(self, list_id: UUID, current_user_id: UUID) -> List | None:
        # TODO: добавить проверку прав
        return await self._repo.get_by_id(list_id)

    async def get_by_board(self, board_id: UUID, current_user_id: UUID, include_archived: bool = False) -> list[List]:
        # TODO: добавить проверку прав
        return await self._repo.get_by_board(board_id, include_archived)

    async def get_active_by_board(self, board_id: UUID, current_user_id: UUID) -> list[List]:
        # TODO: добавить проверку прав
        return await self._repo.get_active_by_board(board_id)

    async def get_archived_by_board(self, board_id: UUID, current_user_id: UUID) -> list[List]:
        # TODO: добавить проверку прав
        return await self._repo.get_archived_by_board(board_id)

    async def update(self, list_id: UUID, data: ListUpdate, current_user_id: UUID) -> List:
        # TODO: добавить проверку прав (доступ к доске)
        current = await self._repo.get_by_id(list_id)
        if not current:
            raise ValueError("Колонка не найдена")

        fields = {}
        if data.name is not None and data.name != current.name:
            fields["name"] = data.name
        if data.position is not None and data.position != current.position:
            fields["position"] = data.position
        if data.wip_limit is not None and data.wip_limit != current.wip_limit:
            fields["wip_limit"] = data.wip_limit
        if data.is_archived is not None and data.is_archived != current.is_archived:
            fields["is_archived"] = data.is_archived

        if not fields:
            return current

        return await self._repo.update_fields(list_id, fields, data.version)

    async def reorder(self, board_id: UUID, list_ids: list[UUID], current_user_id: UUID) -> list[List]:
        # TODO: добавить проверку прав (доступ к доске)
        updates = []
        for index, list_id in enumerate(list_ids, start=1):
            updates.append({
                "id": list_id,
                "position": Decimal(str(index))
            })

        await self._repo.update_positions(board_id, updates)
        return await self._repo.get_active_by_board(board_id)

    async def delete(self, list_id: UUID, current_user_id: UUID) -> None:
        # TODO: добавить проверку прав (доступ к доске)
        list_obj = await self._repo.get_by_id(list_id)
        if not list_obj:
            raise ValueError("Колонка не найдена")
        await self._repo.delete(list_id)