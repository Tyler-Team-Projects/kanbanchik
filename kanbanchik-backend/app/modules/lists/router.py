from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from dishka.integrations.fastapi import FromDishka, inject

from app.modules.lists.schemas import ListCreate, ListUpdate, ListResponse, ListMove
from app.modules.lists.service import IListService


router = APIRouter(prefix="/lists", tags=["lists"])


@router.post("/create", response_model=ListResponse, status_code=201)
@inject
async def create_list(
    data: ListCreate,
    service: FromDishka[IListService] = None,
):
    try:
        list = await service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ListResponse.model_validate(list)


@router.get("/get_list_id", response_model=ListResponse)
@inject
async def get_list_by_id(
    list_id: UUID,
    service: FromDishka[IListService] = None,
):
    list = await service.get_by_id(list_id)
    if not list:
        raise HTTPException(status_code=404, detail="Колонка не найдена")
    return ListResponse.model_validate(list)


@router.get("/get_all_by_board", response_model=list[ListResponse])
@inject
async def get_lists_by_board(
    board_id: UUID,
    include_archived: bool = Query(False, description="Включить архивные колонки"),
    service: FromDishka[IListService] = None,
):
    lists = await service.get_by_board(board_id, include_archived)
    return [ListResponse.model_validate(l) for l in lists]


@router.get("/get_active_by_board", response_model=list[ListResponse])
@inject
async def get_active_lists_by_board(
    board_id: UUID,
    service: FromDishka[IListService] = None,
):
    lists = await service.get_active_by_board(board_id)
    return [ListResponse.model_validate(l) for l in lists]


@router.get("/get_archived_by_board", response_model=list[ListResponse])
@inject
async def get_archived_lists_by_board(
    board_id: UUID,
    service: FromDishka[IListService] = None,
):
    lists = await service.get_archived_by_board(board_id)
    return [ListResponse.model_validate(l) for l in lists]


@router.patch("/update", response_model=ListResponse)
@inject
async def update_list(
    list_id: UUID,
    data: ListUpdate,
    service: FromDishka[IListService] = None,
):
    try:
        list = await service.update(list_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ListResponse.model_validate(list)


@router.patch("/move", response_model=ListResponse)
@inject
async def move_list(
    list_id: UUID,
    data: ListMove,
    service: FromDishka[IListService] = None,
):
    try:
        list = await service.move(list_id, data.new_position)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ListResponse.model_validate(list)


@router.delete("/delete", status_code=204)
@inject
async def delete_list(
    list_id: UUID,
    service: FromDishka[IListService] = None,
):
    try:
        await service.delete(list_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return