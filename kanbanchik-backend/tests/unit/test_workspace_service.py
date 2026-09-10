import pytest
from uuid import UUID

from uuid_extension import uuid7

from app.core.exceptions import (
    WorkspaceNotFoundException,
    PermissionDeniedException,
)
from app.modules.workspaces.service import WorkspaceService
from app.modules.workspaces.repository import IWorkspaceRepository
from app.modules.workspaces.schemas import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceRole,
)
from app.modules.workspaces.models import Workspace, WorkspaceMember

class FakeWorkspaceRepository(IWorkspaceRepository):
    def __init__(self):
        self._workspaces: dict[str, Workspace] = {}
        self._members: dict[tuple[str,str], WorkspaceMember] = {}