from uuid import UUID

from fastapi import APIRouter, Query, Depends
from dishka.integrations.fastapi import FromDishka, inject

from app.api.deps import get_current_user
from app.api.schemas import CurrentUser
from app.modules.lists.schemas import ListCreate, ListUpdate, ListResponse, ListReorder
from app.modules.lists.service import IListService

router = APIRouter(prefix="/lists", tags=["lists"])


@router.post("/create", response_model=ListResponse, status_code=201)
@inject
async def create_list(
    data: ListCreate,
    service: FromDishka[IListService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    list_obj = await service.create(data, current_user.id)
    return ListResponse.model_validate(list_obj)


@router.get("/get_list_id", response_model=ListResponse)
@inject
async def get_list_by_id(
    list_id: UUID,
    service: FromDishka[IListService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    list_obj = await service.get_by_id(list_id, current_user.id)
    return ListResponse.model_validate(list_obj)


@router.get("/get_all_by_board", response_model=list[ListResponse])
@inject
async def get_lists_by_board(
    board_id: UUID,
    include_archived: bool = Query(False, description="Включить архивные колонки"),
    service: FromDishka[IListService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    lists = await service.get_by_board(board_id, current_user.id, include_archived)
    return [ListResponse.model_validate(l) for l in lists]


@router.get("/get_active_by_board", response_model=list[ListResponse])
@inject
async def get_active_lists_by_board(
    board_id: UUID,
    service: FromDishka[IListService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    lists = await service.get_active_by_board(board_id, current_user.id)
    return [ListResponse.model_validate(l) for l in lists]


@router.get("/get_archived_by_board", response_model=list[ListResponse])
@inject
async def get_archived_lists_by_board(
    board_id: UUID,
    service: FromDishka[IListService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    lists = await service.get_archived_by_board(board_id, current_user.id)
    return [ListResponse.model_validate(l) for l in lists]


@router.patch("/update", response_model=ListResponse)
@inject
async def update_list(
    list_id: UUID,
    data: ListUpdate,
    service: FromDishka[IListService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    list_obj = await service.update(list_id, data, current_user.id)
    return ListResponse.model_validate(list_obj)


@router.patch("/reorder", response_model=list[ListResponse])
@inject
async def reorder_lists(
    board_id: UUID,
    data: ListReorder,
    service: FromDishka[IListService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    lists = await service.reorder(board_id, data.list_ids, current_user.id)
    return [ListResponse.model_validate(l) for l in lists]


@router.delete("/delete", status_code=204)
@inject
async def delete_list(
    list_id: UUID,
    service: FromDishka[IListService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    await service.delete(list_id, current_user.id)
    return