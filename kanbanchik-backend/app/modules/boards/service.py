from typing import Protocol
from uuid import UUID

from app.modules.boards.models import Board
from app.modules.boards.schemas import BoardCreate, BoardUpdate
from app.modules.boards.repository import IBoardRepository


class IBoardService(Protocol):
    async def create(self, data: BoardCreate) -> Board: ...
    async def get_by_id(self, board_id: UUID) -> Board | None: ...
    async def get_by_workspace(self, workspace_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_all_active(self, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_archived(self, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def update(self, board_id: UUID, data: BoardUpdate) -> Board: ...
    async def delete(self, board_id: UUID) -> None: ...

class BoardService:
    def __init__(self, repo: IBoardRepository):
        self._repo = repo

    async def create(self, data: BoardCreate) -> Board:
        board = Board(
            workspace_id=data.workspace_id,
            name=data.name,
            description=data.description,
            background_color=data.background_color,
            background_image_url=data.background_image_url,
        )
        return await self._repo.create(board)

    async def get_by_id(self, board_id: UUID) -> Board | None:
        return await self._repo.get_by_id(board_id)

    async def get_by_workspace(self, workspace_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]:
        return await self._repo.get_by_workspace(workspace_id, skip, limit)

    async def get_all_active(self, skip: int = 0, limit: int = 100) -> list[Board]:
        return await self._repo.get_all_active(skip, limit)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Board]:
        return await self._repo.get_all(skip, limit)

    async def get_archived(self, skip: int = 0, limit: int = 100) -> list[Board]:
        return await self._repo.get_archived(skip, limit)

    async def update(self, board_id: UUID, data: BoardUpdate) -> Board:
        board = await self._repo.get_by_id(board_id)
        if not board:
            raise ValueError("Доска не найдена")

        if data.name is not None:
            board.name = data.name
        if data.description is not None:
            board.description = data.description
        if data.background_color is not None:
            board.background_color = data.background_color
        if data.background_image_url is not None:
            board.background_image_url = data.background_image_url
        if data.is_archived is not None:
            board.is_archived = data.is_archived

        return await self._repo.update(board)

    async def delete(self, board_id: UUID) -> None:
        board = await self._repo.get_by_id(board_id)
        if not board:
            raise ValueError("Доска не найдена")
        await self._repo.delete(board_id)