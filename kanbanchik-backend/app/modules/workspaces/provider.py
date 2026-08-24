from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspaces.repository import IWorkspaceRepository, WorkspaceRepository
from app.modules.workspaces.service import IWorkspaceService, WorkspaceService
from app.modules.users.repository import IUserRepository


class WorkspacesProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IWorkspaceRepository)
    async def get_workspace_repo(self, session: AsyncSession) -> IWorkspaceRepository:
        return WorkspaceRepository(session)

    @provide(scope=Scope.REQUEST, provides=IWorkspaceService)
    async def get_workspace_service(
        self,
        repo: IWorkspaceRepository,
        user_repo: IUserRepository
    ) -> IWorkspaceService:
        return WorkspaceService(repo, user_repo)