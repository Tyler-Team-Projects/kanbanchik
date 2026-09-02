from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from dishka.integrations.fastapi import FromDishka, inject

from app.api.deps import get_current_user
from app.api.schemas import CurrentUser
from app.modules.boards.schemas import BoardCreate, BoardUpdate, BoardResponse
from app.modules.boards.service import IBoardService

router = APIRouter(prefix="/boards", tags=["boards"])


@router.post("/create", response_model=BoardResponse, status_code=201)
@inject
async def create_board(
    data: BoardCreate,
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        board = await service.create(data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BoardResponse.model_validate(board)


@router.get("/get_board_id", response_model=BoardResponse)
@inject
async def get_board_by_id(
    board_id: UUID,
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    board = await service.get_by_id(board_id, current_user.id)
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
    current_user: CurrentUser = Depends(get_current_user),
):
    boards = await service.get_by_workspace(workspace_id, current_user.id, skip, limit)
    return [BoardResponse.model_validate(b) for b in boards]


@router.get("/get_all_active", response_model=list[BoardResponse])
@inject
async def get_all_active_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    boards = await service.get_all_active(current_user.id, skip, limit)
    return [BoardResponse.model_validate(b) for b in boards]


@router.get("/get_archived", response_model=list[BoardResponse])
@inject
async def get_archived_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    boards = await service.get_archived(current_user.id, skip, limit)
    return [BoardResponse.model_validate(b) for b in boards]


@router.get("/get_all_boards", response_model=list[BoardResponse])
@inject
async def get_all_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    boards = await service.get_all(current_user.id, skip, limit)
    return [BoardResponse.model_validate(b) for b in boards]


@router.patch("/update", response_model=BoardResponse)
@inject
async def update_board(
    board_id: UUID,
    data: BoardUpdate,
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        board = await service.update(board_id, data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BoardResponse.model_validate(board)


@router.patch("/archive", response_model=BoardResponse)
@inject
async def archive_board(
    board_id: UUID,
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        board = await service.archive(board_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BoardResponse.model_validate(board)


@router.patch("/restore", response_model=BoardResponse)
@inject
async def restore_board(
    board_id: UUID,
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        board = await service.restore(board_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return BoardResponse.model_validate(board)


@router.delete("/delete", status_code=204)
@inject
async def delete_board(
    board_id: UUID,
    service: FromDishka[IBoardService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        await service.delete(board_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return