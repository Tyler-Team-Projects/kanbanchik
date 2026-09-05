from fastapi import APIRouter, Query, Depends

from app.api.deps import get_current_user
from app.api.schemas import CurrentUser
from dishka.integrations.fastapi import FromDishka, inject
from uuid import UUID

from app.modules.workspaces.schemas import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    WorkspaceMemberCreate, WorkspaceMemberUpdate, WorkspaceMemberResponse
)
from app.modules.workspaces.service import IWorkspaceService
from app.core.exceptions import PermissionDeniedException

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=201)
@inject
async def create_workspace(
    data: WorkspaceCreate,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    workspace = await service.create(data, current_user.id)
    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
@inject
async def get_workspace(
    workspace_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    load_relations: bool = Query(False, description="Load members and boards"),
    current_user: CurrentUser = Depends(get_current_user),
):
    workspace = await service.get_by_id(workspace_id, current_user.id, load_relations)
    return WorkspaceResponse.model_validate(workspace)


@router.get("/user/{user_id}", response_model=list[WorkspaceResponse])
@inject
async def get_user_workspaces(
    user_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise PermissionDeniedException(
            "Доступ запрещен: вы можете просматривать только свои рабочие пространства"
        )
    workspaces = await service.get_user_workspaces(user_id)
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
@inject
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    workspace = await service.update(workspace_id, data, current_user.id)
    return WorkspaceResponse.model_validate(workspace)


@router.post("/{workspace_id}/archive", response_model=WorkspaceResponse)
@inject
async def archive_workspace(
    workspace_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    workspace = await service.archive(workspace_id, current_user.id)
    return WorkspaceResponse.model_validate(workspace)

@router.delete("/{workspace_id}", status_code=204)
@inject
async def delete_workspace(
    workspace_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    await service.delete(workspace_id, current_user.id)
    return


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=201)
@inject
async def add_member(
    workspace_id: UUID,
    data: WorkspaceMemberCreate,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    member = await service.add_member(workspace_id, data, current_user.id)
    return WorkspaceMemberResponse.model_validate(member)


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
@inject
async def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    await service.remove_member(workspace_id, user_id, current_user.id)
    return


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
@inject
async def update_member_role(
    workspace_id: UUID,
    user_id: UUID,
    data: WorkspaceMemberUpdate,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    member = await service.update_member_role(workspace_id, user_id, data, current_user.id)
    return WorkspaceMemberResponse.model_validate(member)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
@inject
async def get_members(
    workspace_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    members = await service.get_members(workspace_id, current_user.id)
    return [WorkspaceMemberResponse.model_validate(m) for m in members]