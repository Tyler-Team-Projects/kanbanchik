from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from dishka.integrations.fastapi import FromDishka, inject

from app.modules.boards.schemas import BoardCreate, BoardUpdate, BoardResponse
from app.modules.boards.service import IBoardService


router = APIRouter(prefix="/boards", tags=["boards"])


@router.post("/create", response_model=BoardResponse, status_code=201)
@inject
async def create_board(
    data: BoardCreate,
    service: FromDishka[IBoardService] = None,
):
    try:
        board = await service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BoardResponse.model_validate(board)


@router.get("/get_board_id", response_model=BoardResponse)
@inject
async def get_board_by_id(
    board_id: UUID,
    service: FromDishka[IBoardService] = None,
):
    board = await service.get_by_id(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")
    return BoardResponse.model_validate(board)


@router.get("/get_all_by_workspace", response_model=list[BoardResponse])
@inject
async def get_boards_by_workspace(
    workspace_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IBoardService] = None,
):
    boards = await service.get_by_workspace(workspace_id, skip, limit)
    return [BoardResponse.model_validate(b) for b in boards]


@router.get("/get_all_active", response_model=list[BoardResponse])
@inject
async def get_all_active_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IBoardService] = None,
):
    boards = await service.get_all_active(skip, limit)
    return [BoardResponse.model_validate(b) for b in boards]


@router.get("/get_archived", response_model=list[BoardResponse])
@inject
async def get_archived_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IBoardService] = None,
):
    boards = await service.get_archived(skip, limit)
    return [BoardResponse.model_validate(b) for b in boards]

@router.get("/get_all_boards", response_model=list[BoardResponse])
@inject
async def get_all_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IBoardService] = None,
):
    """Получить все доски (с пагинацией, без фильтрации по is_archived)."""
    boards = await service.get_all(skip, limit)
    return [BoardResponse.model_validate(b) for b in boards]
@router.patch("/update", response_model=BoardResponse)
@inject
async def update_board(
    board_id: UUID,
    data: BoardUpdate,
    service: FromDishka[IBoardService] = None,
):
    try:
        board = await service.update(board_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BoardResponse.model_validate(board)


@router.delete("/delete", status_code=204)
@inject
async def delete_board(
    board_id: UUID,
    service: FromDishka[IBoardService] = None,
):
    try:
        await service.delete(board_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return