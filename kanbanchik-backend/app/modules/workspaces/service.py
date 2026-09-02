from typing import Protocol
from uuid import UUID
from app.modules.workspaces.models import Workspace, WorkspaceMember
from app.modules.workspaces.schemas import (
    WorkspaceCreate, WorkspaceUpdate,
    WorkspaceMemberCreate, WorkspaceMemberUpdate,
    WorkspaceRole
)
from app.modules.workspaces.repository import IWorkspaceRepository
from app.modules.users.repository import IUserRepository  # для проверки существования пользователя


class IWorkspaceService(Protocol):
    async def create(self, data: WorkspaceCreate, owner_id: UUID) -> Workspace: ...
    async def get_by_id(self, workspace_id: UUID, current_user_id: UUID, load_relations: bool = False) -> Workspace | None: ...
    async def get_by_owner(self, owner_id: UUID) -> list[Workspace]: ...
    async def get_user_workspaces(self, user_id: UUID) -> list[Workspace]: ...
    async def update(self, workspace_id: UUID, data: WorkspaceUpdate, current_user_id: UUID) -> Workspace: ...
    async def archive(self, workspace_id: UUID, current_user_id: UUID) -> Workspace: ...
    async def delete(self, workspace_id: UUID, current_user_id: UUID) -> None: ...
    # Управление участниками
    async def add_member(self, workspace_id: UUID, data: WorkspaceMemberCreate, current_user_id: UUID) -> WorkspaceMember: ...
    async def remove_member(self, workspace_id: UUID, user_id_to_remove: UUID, current_user_id: UUID) -> None: ...
    async def update_member_role(self, workspace_id: UUID, user_id_to_update: UUID, data: WorkspaceMemberUpdate, current_user_id: UUID) -> WorkspaceMember: ...
    async def get_members(self, workspace_id: UUID, current_user_id: UUID) -> list[WorkspaceMember]: ...


class WorkspaceService:
    def __init__(self, repo: IWorkspaceRepository, user_repo: IUserRepository):
        self._repo = repo
        self._user_repo = user_repo

    async def create(self, data: WorkspaceCreate, owner_id: UUID) -> Workspace:
        workspace = Workspace(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            color=data.color,
        )
        # Сначала сохраняем workspace, чтобы получить id
        workspace = await self._repo.create(workspace)
        # Затем добавляем владельца как участника с ролью owner
        await self._repo.add_member(workspace.id, owner_id, WorkspaceRole.OWNER.value)
        return workspace

    async def get_by_id(
            self,
            workspace_id: UUID,
            current_user_id: UUID,
        load_relations: bool = False
    ) -> Workspace | None:
        await self._check_role(workspace_id, current_user_id, WorkspaceRole.VIEWER)
        return await self._repo.get_by_id(workspace_id, load_relations)

    async def get_by_owner(self, owner_id: UUID) -> list[Workspace]:
        return await self._repo.get_by_owner(owner_id, include_archived=False)

    async def get_user_workspaces(self, user_id: UUID) -> list[Workspace]:
        return await self._repo.get_user_workspaces(user_id, include_archived=False)

    async def update(self, workspace_id: UUID, data: WorkspaceUpdate, current_user_id: UUID) -> Workspace:
        await self._check_role(workspace_id, current_user_id, WorkspaceRole.ADMIN)
        workspace = await self._repo.get_by_id(workspace_id)
        if not workspace:
            raise ValueError("Рабочее пространство не найдено")
        # Обновляем поля
        if data.name is not None:
            workspace.name = data.name
        if data.description is not None:
            workspace.description = data.description
        if data.color is not None:
            workspace.color = data.color
        if data.is_archived is not None:
            workspace.is_archived = data.is_archived
        return await self._repo.update(workspace)

    async def archive(self, workspace_id: UUID, current_user_id: UUID) -> Workspace:
        await self._check_role(workspace_id, current_user_id, WorkspaceRole.OWNER)
        workspace = await self._repo.get_by_id(workspace_id)
        if not workspace:
            raise ValueError("Рабочее пространство не найдено")
        workspace.is_archived = True
        return await self._repo.update(workspace)

    async def delete(self, workspace_id: UUID, current_user_id: UUID) -> None:
        await self._check_role(workspace_id, current_user_id, WorkspaceRole.OWNER)
        workspace = await self._repo.get_by_id(workspace_id)
        if not workspace:
            raise ValueError("Рабочее пространство не найдено")
        await self._repo.delete(workspace_id)

    # Управление участниками
    async def add_member(self, workspace_id: UUID, data: WorkspaceMemberCreate, current_user_id: UUID) -> WorkspaceMember:
        # Проверка прав: только владелец или админ может добавлять
        await self._check_role(workspace_id, current_user_id, WorkspaceRole.ADMIN)
        # Проверяем, что пользователь существует
        user = await self._user_repo.get_by_id(data.user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        # Проверяем, не состоит ли уже
        existing = await self._repo.get_member(workspace_id, data.user_id)
        if existing:
            raise ValueError("Пользователь уже состоит в рабочем пространстве")
        return await self._repo.add_member(workspace_id, data.user_id, data.role.value)

    async def remove_member(self, workspace_id: UUID, user_id_to_remove: UUID, current_user_id: UUID) -> None:
        # Проверка прав: владелец или админ, либо сам пользователь удаляет себя
        if current_user_id != user_id_to_remove:
            await self._check_role(workspace_id, current_user_id, WorkspaceRole.ADMIN)
        # Нельзя удалить владельца (если только он не передаст права)
        member = await self._repo.get_member(workspace_id, user_id_to_remove)
        if not member:
            raise ValueError("Участник не найден")
        if member.role == WorkspaceRole.OWNER.value:
            raise ValueError("Нельзя удалить владельца пространства")
        await self._repo.remove_member(workspace_id, user_id_to_remove)

    async def update_member_role(
            self,
            workspace_id: UUID,
            user_id_to_update: UUID,
            data: WorkspaceMemberUpdate,
            current_user_id: UUID
    ) -> WorkspaceMember:
        await self._check_role(workspace_id, current_user_id, WorkspaceRole.ADMIN)

        workspace = await self._repo.get_by_id(workspace_id)
        if not workspace:
            raise ValueError("Рабочее пространство не найдено")

        member = await self._repo.get_member(workspace_id, user_id_to_update)
        if not member:
            raise ValueError("Участник не найден")

        # Запрещаем изменять роль владельца (если это не сам владелец и не передача прав)
        if member.role == WorkspaceRole.OWNER.value and current_user_id != workspace.owner_id:
            raise PermissionError("Только владелец может изменить свою роль")

        # Если мы назначаем нового владельца
        if data.role == WorkspaceRole.OWNER:
            # Проверяем, что текущий пользователь – текущий владелец
            if current_user_id != workspace.owner_id:
                raise PermissionError("Только сам владелец может передать свои права")
            # Обновляем owner_id в таблице workspaces
            workspace.owner_id = user_id_to_update
            await self._repo.update(workspace)  # коммитим изменение владельца

            # Меняем роль старого владельца на 'admin' (или другую роль по выбору)
            old_owner_member = await self._repo.get_member(workspace_id, current_user_id)
            if old_owner_member:
                old_owner_member.role = WorkspaceRole.ADMIN.value
                await self._repo.update_member_role(workspace_id, current_user_id, old_owner_member.role)

            # Устанавливаем роль новому владельцу
            member.role = WorkspaceRole.OWNER.value
        else:
            # Если мы меняем роль не на owner, просто обновляем
            member.role = data.role.value

        return await self._repo.update_member_role(workspace_id, user_id_to_update, member.role)

    async def get_members(self, workspace_id: UUID, current_user_id: UUID) -> list[WorkspaceMember]:
        await self._check_role(workspace_id, current_user_id, WorkspaceRole.VIEWER)
        return await self._repo.get_members(workspace_id)

    # Вспомогательные методы для проверки прав
    async def _check_role(
            self,
            workspace_id: UUID,
            user_id: UUID,
            required_role: WorkspaceRole
    ) -> None:
        """Проверяет, имеет ли пользователь необходимую роль в workspace"""
        workspace = await self._repo.get_by_id(workspace_id)
        if not workspace:
            raise ValueError("Рабочее пространство не найдено")
        # У владельца есть все права на пространство
        if workspace and workspace.owner_id == user_id:
            return

        member = await self._repo.get_member(workspace_id, user_id)
        if not member:
            raise PermissionError("Пользователь не является участником данного рабочего пространства")


        role_hierarchy = {
            WorkspaceRole.OWNER: 4,
            WorkspaceRole.ADMIN: 3,
            WorkspaceRole.MEMBER: 2,
            WorkspaceRole.VIEWER: 1,
        }

        if role_hierarchy.get(WorkspaceRole(member.role), 0) < role_hierarchy.get(required_role, 0):
            raise PermissionError(f"Необходимая роль: {required_role}, роль пользователя: {member.role}")
