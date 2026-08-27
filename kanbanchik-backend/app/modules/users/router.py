from fastapi import APIRouter, HTTPException, Query, Depends
from app.api.deps import get_current_user
from app.api.schemas import CurrentUser

from dishka.integrations.fastapi import FromDishka, inject
from uuid import UUID

from app.modules.users.schemas import UserCreate, UserUpdate, UserResponse
from app.modules.users.service import IUserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=201)
@inject
async def register(
    data: UserCreate,
    service: FromDishka[IUserService] = None,
):
    try:
        user = await service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)

@router.get("/user_id", response_model=UserResponse)
@inject
async def get_user_by_id(
    user_id: UUID,
    service: FromDishka[IUserService] = None,
):
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserResponse.model_validate(user)

@router.get("/user_username", response_model=UserResponse)
@inject
async def get_user_by_username(
    username: str,
    service: FromDishka[IUserService] = None,
):
    user = await service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@router.patch("/update_me", response_model=UserResponse)
@inject
async def update_me(
    data: UserUpdate,
    service: FromDishka[IUserService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        user = await service.update_profile(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UserResponse.model_validate(user)


@router.delete("/deactivate_me", status_code=204)
@inject
async def deactivate_me(
    service: FromDishka[IUserService] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    try:
        await service.deactivate(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return


@router.get("/get_all_users", response_model=list[UserResponse])
@inject
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IUserService] = None,
    # TODO: заменить на реального пользователя из токена
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),  # временная заглушка
):
    user = await service.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@router.get("/user_id", response_model=UserResponse)
@inject
async def get_user(
    user_id: UUID,
    service: FromDishka[IUserService] = None,
):
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserResponse.model_validate(user)

@router.get("/user_username", response_model=UserResponse)
@inject
async def get_user(
    username: str,
    service: FromDishka[IUserService] = None,
):
    user = await service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@router.patch("/update_me", response_model=UserResponse)
@inject
async def update_me(
    data: UserUpdate,
    service: FromDishka[IUserService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),  # заглушка
):
    try:
        user = await service.update_profile(current_user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UserResponse.model_validate(user)


@router.delete("/deactivate_me", status_code=204)
@inject
async def deactivate_me(
    service: FromDishka[IUserService] = None,
    current_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000"),  # заглушка
):
    try:
        await service.deactivate(current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return


@router.get("/get_all_users", response_model=list[UserResponse])
@inject
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IUserService] = None,
):
    users = await service.get_all(skip, limit)
    return [UserResponse.model_validate(u) for u in users]