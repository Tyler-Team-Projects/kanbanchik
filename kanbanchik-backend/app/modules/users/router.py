from fastapi import APIRouter, HTTPException, Query, Depends
from app.api.deps import get_current_user
from app.api.schemas import CurrentUser

from dishka.integrations.fastapi import FromDishka, inject
from uuid import UUID

from app.modules.users.schemas import UserCreate, UserUpdate, UserResponse, ChangePassword
from app.modules.users.service import IUserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=201)
@inject
async def register(
    data: UserCreate,
    service: FromDishka[IUserService] = None,
):
    user = await service.register(data)
    return UserResponse.model_validate(user)


@router.post("/me/password", response_model=UserResponse)
@inject
async def change_password(
    data: ChangePassword,
    service: FromDishka[IUserService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    user = await service.change_password(current_user.id, data.old_password, data.new_password)
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
@inject
async def update_me(
    data: UserUpdate,
    service: FromDishka[IUserService] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    user = await service.update_profile(current_user.id, data)
    return UserResponse.model_validate(user)


@router.delete("/me", status_code=204)
@inject
async def deactivate_me(
    service: FromDishka[IUserService] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    await service.deactivate(current_user.id)
    return


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)


@router.get("/users/{user_id}", response_model=UserResponse)
@inject
async def get_user_by_id(
    user_id: UUID,
    service: FromDishka[IUserService] = None,
):
    user = await service.get_by_id(user_id)
    return UserResponse.model_validate(user)


@router.get("/?username={username}", response_model=UserResponse)
@inject
async def get_user_by_username(
    username: str,
    service: FromDishka[IUserService] = None,
):
    user = await service.get_by_username(username)
    return UserResponse.model_validate(user)


@router.get("/", response_model=list[UserResponse])
@inject
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: FromDishka[IUserService] = None,
):
    users = await service.get_all(skip, limit)
    return [UserResponse.model_validate(u) for u in users]