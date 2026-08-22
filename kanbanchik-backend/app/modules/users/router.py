from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka, inject

from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.users.service import UserService, IUserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/create", response_model=UserResponse)
@inject
async def create_user(
    data: UserCreate,
    service: FromDishka[IUserService] = None,
):
    user = await service.register(data)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
@inject
async def get_me(
    service: FromDishka[IUserService] = None,
    # TODO: потом сюда прилетит current_user: FromDishka[User]
):
    # Заглушка — потом заменим на реального пользователя
    return {"id": "00000000-0000-0000-0000-000000000000", "email": "test@test.com", "username": "test", "name": None, "created_at": "2024-01-01T00:00:00"}