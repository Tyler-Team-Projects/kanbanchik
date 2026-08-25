from typing import Protocol
from uuid import UUID
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.workspaces.models import Workspace, WorkspaceMember
from app.modules.users.models import User


class IWorkspaceRepository(Protocol):
    async def get_by_id(self, workspace_id: UUID, load_relations: bool = False) -> Workspace | None: ...
    async def get_by_owner(self, owner_id: UUID, include_archived: bool = False) -> list[Workspace]: ...
    async def get_user_workspaces(self, user_id: UUID, include_archived: bool = False) -> list[Workspace]: ...
    async def create(self, workspace: Workspace) -> Workspace: ...
    async def update(self, workspace: Workspace) -> Workspace: ...
    async def delete(self, workspace_id: UUID) -> None: ...
    # Управление участниками
    async def add_member(self, workspace_id: UUID, user_id: UUID, role: str) -> WorkspaceMember: ...
    async def remove_member(self, workspace_id: UUID, user_id: UUID) -> None: ...
    async def update_member_role(self, workspace_id: UUID, user_id: UUID, new_role: str) -> WorkspaceMember: ...
    async def get_member(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None: ...
    async def get_members(self, workspace_id: UUID) -> list[WorkspaceMember]: ...


class WorkspaceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, workspace_id: UUID, load_relations: bool = False) -> Workspace | None:
        statement = select(Workspace).where(Workspace.id == workspace_id)
        if load_relations:
            statement = statement.options(
                selectinload(Workspace.owner),
                selectinload(Workspace.members).selectinload(WorkspaceMember.user),
                selectinload(Workspace.boards),
            )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: UUID, include_archived: bool = False) -> list[Workspace]:
        statement = select(Workspace).where(Workspace.owner_id == owner_id)
        if not include_archived:
            statement = statement.where(Workspace.is_archived == False)
        statement = statement.order_by(Workspace.created_at)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def get_user_workspaces(self, user_id: UUID, include_archived: bool = False) -> list[Workspace]:
        # Рабочие пространства, где пользователь является владельцем или участником
        subquery = select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user_id)
        statement = select(Workspace).where(
            (Workspace.owner_id == user_id) | (Workspace.id.in_(subquery))
        )
        if not include_archived:
            statement = statement.where(Workspace.is_archived == False)
        statement = statement.distinct().order_by(Workspace.created_at)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def create(self, workspace: Workspace) -> Workspace:
        self._session.add(workspace)
        await self._session.commit()
        await self._session.refresh(workspace)
        return workspace

    async def update(self, workspace: Workspace) -> Workspace:
        await self._session.commit()
        await self._session.refresh(workspace)
        return workspace

    async def delete(self, workspace_id: UUID) -> None:
        await self._session.execute(delete(Workspace).where(Workspace.id == workspace_id))
        await self._session.commit()

    # Методы для участников
    async def add_member(self, workspace_id: UUID, user_id: UUID, role: str) -> WorkspaceMember:
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
        )
        self._session.add(member)
        await self._session.commit()
        await self._session.refresh(member)
        return member

    async def remove_member(self, workspace_id: UUID, user_id: UUID) -> None:
        await self._session.execute(
            delete(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id
            )
        )
        await self._session.commit()

    async def update_member_role(self, workspace_id: UUID, user_id: UUID, new_role: str) -> WorkspaceMember:
        member = await self.get_member(workspace_id, user_id)
        if member:
            member.role = new_role
            await self._session.commit()
            await self._session.refresh(member)
        return member

    async def get_member(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        result = await self._session.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id
            )
            .options(selectinload(WorkspaceMember.workspace))
        )
        return result.scalar_one_or_none()

    async def get_members(self, workspace_id: UUID) -> list[WorkspaceMember]:
        result = await self._session.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.joined_at)
        )
        return result.scalars().all()