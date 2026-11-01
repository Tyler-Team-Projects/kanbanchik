from datetime import datetime, timezone
from uuid import UUID

import pytest
from uuid_extension import uuid7

from app.core.exceptions import (
    WorkspaceNotFoundException,
    PermissionDeniedException,
    WorkspaceMemberAlreadyExistsException,
)
from app.modules.workspaces.service import WorkspaceService
from app.modules.workspaces.repository import IWorkspaceRepository
from app.modules.workspaces.schemas import (
    WorkspaceCreate,
    WorkspaceRole,
    WorkspaceUpdate,
    WorkspaceMemberCreate,
)
from app.modules.workspaces.models import Workspace, WorkspaceMember
from tests.factories import UserFactory


class FakeWorkspaceRepository(IWorkspaceRepository):
    def __init__(self):
        self._workspaces: dict[str, Workspace] = {}
        self._members: dict[tuple[str, str], WorkspaceMember] = {}

    async def get_by_id(
        self, workspace_id: UUID, load_relations: bool = False
    ) -> Workspace | None:
        return self._workspaces.get(str(workspace_id))

    async def get_by_owner(self, owner_id, include_archived=False):
        result = []
        for workspace in self._workspaces.values():
            if workspace.owner_id == owner_id:
                result.append(workspace)
        if not include_archived:
            result = [w for w in result if not w.is_archived]
        result.sort(key=lambda w: w.created_at)
        return result

    async def get_user_workspaces(
        self, user_id: UUID, include_archived: bool = False
    ) -> list[Workspace]:
        result = []
        for workspace in self._workspaces.values():
            if workspace.owner_id == user_id:
                result.append(workspace)

        member_workspace_ids = []
        for (ws_id, uid) in self._members.keys():
            if uid == str(user_id):
                member_workspace_ids.append(ws_id)

        for workspace in self._workspaces.values():
            if str(workspace.id) in member_workspace_ids:
                result.append(workspace)

        seen = set()
        unique = []
        for workspace in result:
            if str(workspace.id) not in seen:
                seen.add(str(workspace.id))
                unique.append(workspace)

        if not include_archived:
            unique = [w for w in unique if not w.is_archived]

        return unique

    async def create(self, workspace: Workspace) -> Workspace:
        if workspace.id is None:
            workspace.id = uuid7()
        if workspace.is_archived is None:
            workspace.is_archived = False
        if workspace.color is None:
            workspace.color = "#3b82f6"
        if workspace.created_at is None:
            workspace.created_at = datetime.now(timezone.utc)
        if workspace.updated_at is None:
            workspace.updated_at = datetime.now(timezone.utc)

        self._workspaces[str(workspace.id)] = workspace
        return workspace

    async def update(self, workspace: Workspace) -> Workspace:
        self._workspaces[str(workspace.id)] = workspace
        return workspace

    async def delete(self, workspace_id: UUID) -> None:
        self._workspaces.pop(str(workspace_id), None)

    async def add_member(
        self, workspace_id: UUID, user_id: UUID, role: str
    ) -> WorkspaceMember:
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
        )
        self._members[(str(workspace_id), str(user_id))] = member
        return member

    async def remove_member(self, workspace_id: UUID, user_id: UUID) -> None:
        self._members.pop((str(workspace_id), str(user_id)), None)

    async def update_member_role(
        self, workspace_id: UUID, user_id: UUID, new_role: str
    ) -> WorkspaceMember | None:
        member = self._members.get((str(workspace_id), str(user_id)))
        if member:
            member.role = new_role
        return member

    async def get_member(
        self, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceMember | None:
        return self._members.get((str(workspace_id), str(user_id)))

    async def get_members(self, workspace_id: UUID) -> list[WorkspaceMember]:
        result = []
        for (ws_id, _), member in self._members.items():
            if ws_id == str(workspace_id):
                result.append(member)
        return result


class FakeUserRepository:
    """Минимальный FakeUserRepository для тестов workspace."""

    def __init__(self):
        self._users: dict[str, object] = {}

    async def get_by_id(self, user_id):
        return self._users.get(str(user_id))

    async def create(self, user):
        self._users[str(user.id)] = user
        return user


@pytest.fixture
def fake_workspace_repo():
    return FakeWorkspaceRepository()


@pytest.fixture
def fake_user_repo():
    return FakeUserRepository()


@pytest.fixture
def workspace_service(fake_workspace_repo, fake_user_repo):
    return WorkspaceService(
        repo=fake_workspace_repo,
        user_repo=fake_user_repo,
    )


async def test_create_workspace_successfully(workspace_service):
    """Создание workspace возвращает объект с корректными полями."""

    owner_id = uuid7()
    data = WorkspaceCreate(
        name="Моё пространство",
        description="Тестовое описание",
        color="#3b82f6",
    )

    workspace = await workspace_service.create(data, owner_id)

    assert workspace.name == "Моё пространство"
    assert workspace.description == "Тестовое описание"
    assert workspace.color == "#3b82f6"
    assert workspace.owner_id == owner_id
    assert workspace.is_archived is False


async def test_create_workspace_assigns_creator_as_owner(
    workspace_service, fake_workspace_repo
):
    """Создание workspace добавляет создателя как участника с ролью owner."""

    owner_id = uuid7()
    data = WorkspaceCreate(name="Моё пространство")

    workspace = await workspace_service.create(data, owner_id)

    member = await fake_workspace_repo.get_member(workspace.id, owner_id)
    assert member is not None
    assert member.role == WorkspaceRole.OWNER.value


async def test_get_workspace_allows_owner_to_access_it(workspace_service):
    """Владелец workspace может получить его по ID."""

    owner_id = uuid7()
    created = await workspace_service.create(
        WorkspaceCreate(name="Моё пространство"), owner_id
    )

    workspace = await workspace_service.get_by_id(created.id, owner_id)

    assert workspace is not None
    assert workspace.id == created.id
    assert workspace.name == "Моё пространство"


async def test_get_user_workspaces_excludes_archived_by_default(
    workspace_service,
):
    """По умолчанию архивные workspace не возвращаются."""

    owner_id = uuid7()
    active = await workspace_service.create(
        WorkspaceCreate(name="Active"), owner_id
    )
    archived = await workspace_service.create(
        WorkspaceCreate(name="Archived"), owner_id
    )
    await workspace_service.archive(archived.id, owner_id)

    workspaces = await workspace_service.get_user_workspaces(owner_id)

    assert len(workspaces) == 1
    assert workspaces[0].id == active.id


async def test_get_workspace_for_non_member_raises_permission_denied(
    workspace_service,
):
    """Не-участник получает PermissionDeniedException."""

    owner_id = uuid7()
    stranger_id = uuid7()
    created = await workspace_service.create(
        WorkspaceCreate(name="Моё пространство"), owner_id
    )

    with pytest.raises(PermissionDeniedException):
        await workspace_service.get_by_id(created.id, stranger_id)


async def test_get_workspace_with_nonexistent_id_raises_not_found(
    workspace_service,
):
    """Несуществующий workspace → WorkspaceNotFoundException."""

    owner_id = uuid7()
    nonexistent_id = uuid7()

    with pytest.raises(WorkspaceNotFoundException):
        await workspace_service.get_by_id(nonexistent_id, owner_id)


async def test_get_user_workspaces_returns_all_owned_workspaces(
    workspace_service,
):
    """Список workspace для owner возвращает все его workspace."""

    owner_id = uuid7()
    await workspace_service.create(
        WorkspaceCreate(name="Пространство 1"), owner_id
    )
    await workspace_service.create(
        WorkspaceCreate(name="Пространство 2"), owner_id
    )

    workspaces = await workspace_service.get_user_workspaces(owner_id)

    assert len(workspaces) == 2
    names = {w.name for w in workspaces}
    assert names == {"Пространство 1", "Пространство 2"}


async def test_get_user_workspaces_for_non_owner_returns_empty_list(
    workspace_service,
):
    """Пользователь без workspace получает пустой список."""

    stranger_id = uuid7()
    workspaces = await workspace_service.get_user_workspaces(stranger_id)
    assert workspaces == []


async def test_archive_workspace_by_owner_successfully_archives_it(
    workspace_service, fake_workspace_repo
):
    """Владелец архивирует workspace — is_archived становится True."""
    owner_id = uuid7()
    created = await workspace_service.create(
        WorkspaceCreate(name="Пространство для архивации"), owner_id
    )

    archived = await workspace_service.archive(created.id, owner_id)

    assert archived.is_archived is True
    stored = await fake_workspace_repo.get_by_id(created.id)
    assert stored.is_archived is True


async def test_archive_workspace_by_admin_raises_permission_denied(
    workspace_service, fake_workspace_repo
):
    """Admin не может архивировать workspace (только owner)."""
    owner_id = uuid7()
    admin_id = uuid7()
    created = await workspace_service.create(
        WorkspaceCreate(name="Моё пространство"), owner_id
    )
    await fake_workspace_repo.add_member(
        created.id,
        admin_id,
        WorkspaceRole.ADMIN.value,
    )

    with pytest.raises(PermissionDeniedException):
        await workspace_service.archive(created.id, admin_id)


async def test_update_workspace_by_owner_updates_fields(
    workspace_service, fake_workspace_repo
):
    """Owner обновляет поля workspace."""

    owner_id = uuid7()
    created = await workspace_service.create(
        WorkspaceCreate(name="Old name"), owner_id
    )
    data = WorkspaceUpdate(name="New name", description="New description")

    updated = await workspace_service.update(created.id, data, owner_id)

    assert updated.name == "New name"
    assert updated.description == "New description"


async def test_update_workspace_by_member_raises_permission_denied(
    workspace_service, fake_workspace_repo
):
    """Member не может обновлять workspace."""

    owner_id = uuid7()
    member_id = uuid7()
    created = await workspace_service.create(
        WorkspaceCreate(name="Name"), owner_id
    )
    await fake_workspace_repo.add_member(
        created.id, member_id, WorkspaceRole.MEMBER.value
    )
    data = WorkspaceUpdate(name="New name")

    with pytest.raises(PermissionDeniedException):
        await workspace_service.update(created.id, data, member_id)


async def test_delete_workspace_by_owner_removes_it(
    workspace_service, fake_workspace_repo
):
    """Owner удаляет workspace."""

    owner_id = uuid7()
    created = await workspace_service.create(
        WorkspaceCreate(name="To delete"), owner_id
    )

    await workspace_service.delete(created.id, owner_id)

    stored = await fake_workspace_repo.get_by_id(created.id)
    assert stored is None


async def test_delete_workspace_by_admin_raises_permission_denied(
    workspace_service, fake_workspace_repo
):
    """Admin не может удалять workspace."""

    owner_id = uuid7()
    admin_id = uuid7()
    created = await workspace_service.create(
        WorkspaceCreate(name="Name"), owner_id
    )
    await fake_workspace_repo.add_member(
        created.id, admin_id, WorkspaceRole.ADMIN.value
    )

    with pytest.raises(PermissionDeniedException):
        await workspace_service.delete(created.id, admin_id)


async def test_add_member_by_owner_adds_member(
    workspace_service, fake_workspace_repo, fake_user_repo
):
    """Owner добавляет нового участника."""

    owner_id = uuid7()
    new_user = UserFactory.build()
    await fake_user_repo.create(new_user)
    created = await workspace_service.create(
        WorkspaceCreate(name="Name"), owner_id
    )
    data = WorkspaceMemberCreate(
        user_id=new_user.id,
        role=WorkspaceRole.MEMBER,
    )

    member = await workspace_service.add_member(created.id, data, owner_id)

    assert member.user_id == new_user.id
    assert member.role == WorkspaceRole.MEMBER.value


async def test_add_member_already_exists_raises_conflict(
    workspace_service, fake_workspace_repo, fake_user_repo
):
    """Участник уже есть → WorkspaceMemberAlreadyExistsException."""

    owner_id = uuid7()
    user = UserFactory.build()
    await fake_user_repo.create(user)
    created = await workspace_service.create(
        WorkspaceCreate(name="Name"), owner_id
    )
    await fake_workspace_repo.add_member(
        created.id, user.id, WorkspaceRole.MEMBER.value
    )
    data = WorkspaceMemberCreate(user_id=user.id, role=WorkspaceRole.MEMBER)

    with pytest.raises(WorkspaceMemberAlreadyExistsException):
        await workspace_service.add_member(created.id, data, owner_id)


async def test_get_by_owner_returns_only_active_workspaces(workspace_service):
    """get_by_owner возвращает только активные workspace."""

    owner_id = uuid7()
    active = await workspace_service.create(
        WorkspaceCreate(name="Active"), owner_id
    )
    archived = await workspace_service.create(
        WorkspaceCreate(name="Archived"), owner_id
    )
    await workspace_service.archive(archived.id, owner_id)

    workspaces = await workspace_service.get_by_owner(owner_id)

    assert len(workspaces) == 1
    assert workspaces[0].id == active.id
