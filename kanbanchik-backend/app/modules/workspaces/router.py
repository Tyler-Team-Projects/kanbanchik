from fastapi import APIRouter, Query
from dishka.integrations.fastapi import FromDishka, inject
from uuid import UUID

from app.modules.workspaces.schemas import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    WorkspaceMemberCreate, WorkspaceMemberUpdate, WorkspaceMemberResponse
)
from app.modules.workspaces.service import IWorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=201)
@inject
async def create_workspace(
    data: WorkspaceCreate,
    service: FromDishka[IWorkspaceService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
    workspace = await service.create(data, current_user_id)
    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
@inject
async def get_workspace(
    workspace_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    load_relations: bool = Query(False, description="Load members and boards"),
):
    workspace = await service.get_by_id(workspace_id, load_relations)
    return WorkspaceResponse.model_validate(workspace)


@router.get("/user/{user_id}", response_model=list[WorkspaceResponse])
@inject
async def get_user_workspaces(
    user_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
):
    workspaces = await service.get_user_workspaces(user_id)
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
@inject
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    service: FromDishka[IWorkspaceService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
    workspace = await service.update(workspace_id, data, current_user_id)
    return WorkspaceResponse.model_validate(workspace)


@router.post("/{workspace_id}/archive", response_model=WorkspaceResponse)
@inject
async def archive_workspace(
    workspace_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
    workspace = await service.archive(workspace_id, current_user_id)
    return WorkspaceResponse.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=204)
@inject
async def delete_workspace(
    workspace_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
    await service.delete(workspace_id, current_user_id)
    return


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=201)
@inject
async def add_member(
    workspace_id: UUID,
    data: WorkspaceMemberCreate,
    service: FromDishka[IWorkspaceService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
    member = await service.add_member(workspace_id, data, current_user_id)
    return WorkspaceMemberResponse.model_validate(member)


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
@inject
async def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
    await service.remove_member(workspace_id, user_id, current_user_id)
    return


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
@inject
async def update_member_role(
    workspace_id: UUID,
    user_id: UUID,
    data: WorkspaceMemberUpdate,
    service: FromDishka[IWorkspaceService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),
):
    member = await service.update_member_role(workspace_id, user_id, data, current_user_id)
    return WorkspaceMemberResponse.model_validate(member)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
@inject
async def get_members(
    workspace_id: UUID,
    service: FromDishka[IWorkspaceService] = None,
):
    members = await service.get_members(workspace_id)
    return [WorkspaceMemberResponse.model_validate(m) for m in members]