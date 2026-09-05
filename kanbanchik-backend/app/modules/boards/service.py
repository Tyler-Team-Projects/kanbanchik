from typing import Protocol
from uuid import UUID

from app.modules.boards.models import Board
from app.modules.boards.schemas import BoardCreate, BoardUpdate
from app.modules.boards.repository import IBoardRepository

from app.core.exceptions import (
    BoardNotFoundException,
    BoardAlreadyArchivedException,
    BoardNotArchivedException,
)


class IBoardService(Protocol):
    async def create(self, data: BoardCreate, current_user_id: UUID) -> Board: ...
    async def get_by_id(self, board_id: UUID, current_user_id: UUID) -> Board | None: ...
    async def get_by_workspace(self, workspace_id: UUID, current_user_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_all_active(self, current_user_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_all(self, current_user_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_archived(self, current_user_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def update(self, board_id: UUID, data: BoardUpdate, current_user_id: UUID) -> Board: ...
    async def archive(self, board_id: UUID, current_user_id: UUID) -> Board: ...
    async def restore(self, board_id: UUID, current_user_id: UUID) -> Board: ...
    async def delete(self, board_id: UUID, current_user_id: UUID) -> None: ...


class BoardService:
    def __init__(self, repo: IBoardRepository):
        self._repo = repo

    async def create(self, data: BoardCreate, current_user_id: UUID) -> Board:
        # TODO: добавить проверку прав (доступ к workspace)
        board = Board(
            workspace_id=data.workspace_id,
            name=data.name,
            description=data.description,
            background_color=data.background_color,
            background_image_url=data.background_image_url,
        )
        return await self._repo.create(board)

    async def get_by_id(self, board_id: UUID, current_user_id: UUID) -> Board | None:
        # TODO: добавить проверку прав
        return await self._repo.get_by_id(board_id)

    async def get_by_workspace(self, workspace_id: UUID, current_user_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]:
        # TODO: добавить проверку прав
        return await self._repo.get_by_workspace(workspace_id, skip, limit)

    async def get_all_active(self, current_user_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]:
        # TODO: добавить проверку прав (возможно, только админам)
        return await self._repo.get_all_active(skip, limit)

    async def get_all(self, current_user_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]:
        # TODO: добавить проверку прав (возможно, только админам)
        return await self._repo.get_all(skip, limit)

    async def get_archived(self, current_user_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]:
        # TODO: добавить проверку прав (возможно, только админам)
        return await self._repo.get_archived(skip, limit)

    async def update(self, board_id: UUID, data: BoardUpdate, current_user_id: UUID) -> Board:
        # TODO: добавить проверку прав (доступ к workspace)
        board = await self._repo.get_by_id(board_id)
        if not board:
            raise BoardNotFoundException(str(board_id))

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

    async def archive(self, board_id: UUID, current_user_id: UUID) -> Board:
        # TODO: добавить проверку прав (доступ к workspace)
        board = await self._repo.get_by_id(board_id)
        if not board:
            raise BoardNotFoundException(str(board_id))
        if board.is_archived:
            raise BoardAlreadyArchivedException()
        board.is_archived = True
        return await self._repo.update(board)

    async def restore(self, board_id: UUID, current_user_id: UUID) -> Board:
        # TODO: добавить проверку прав (доступ к workspace)
        board = await self._repo.get_by_id(board_id)
        if not board:
            raise BoardNotFoundException(str(board_id))
        if not board.is_archived:
            raise BoardNotArchivedException()
        board.is_archived = False
        return await self._repo.update(board)

    async def delete(self, board_id: UUID, current_user_id: UUID) -> None:
        # TODO: добавить проверку прав (доступ к workspace)
        board = await self._repo.get_by_id(board_id)
        if not board:
            raise BoardNotFoundException(str(board_id))
        await self._repo.delete(board_id)