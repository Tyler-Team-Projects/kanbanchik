from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.boards.models import Board


class IBoardRepository(Protocol):
    async def get_by_id(self, board_id: UUID) -> Board | None: ...
    async def get_by_workspace(self, workspace_id: UUID, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_all_active(self, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_all(self, workspace_id: UUID | None = None, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def get_archived(self, skip: int = 0, limit: int = 100) -> list[Board]: ...
    async def create(self, board: Board) -> Board: ...
    async def update(self, board: Board) -> Board: ...
    async def delete(self, board_id: UUID) -> None: ...


class BoardRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, board_id: UUID) -> Board | None:
        result = await self._session.execute(
            select(Board).where(Board.id == board_id)
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Board]:
        result = await self._session.execute(
            select(Board)
            .where(Board.workspace_id == workspace_id)
            .order_by(Board.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all_active(
        self,
        workspace_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Board]:
        """Получить все активные доски (is_archived=False)."""
        query = select(Board).where(Board.is_archived == False)
        if workspace_id:
            query = query.where(Board.workspace_id == workspace_id)
        query = query.order_by(Board.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_all(
            self,
            workspace_id: UUID | None = None,
            skip: int = 0,
            limit: int = 100,
    ) -> list[Board]:
        """Получить все доски (без фильтрации по is_archived)."""
        query = select(Board)
        if workspace_id:
            query = query.where(Board.workspace_id == workspace_id)
        query = query.order_by(Board.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def create(self, board: Board) -> Board:
        self._session.add(board)
        await self._session.commit()
        await self._session.refresh(board)
        return board

    async def update(self, board: Board) -> Board:
        await self._session.commit()
        await self._session.refresh(board)
        return board

    async def delete(self, board_id: UUID) -> None:
        await self._session.execute(
            delete(Board).where(Board.id == board_id)
        )
        await self._session.commit()