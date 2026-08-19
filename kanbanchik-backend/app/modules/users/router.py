from fastapi import APIRouter
from dishka.integrations.fastapi import FromDishka

from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.users.service import IUserService


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    service: FromDishka[IUserService],
):
    return await service.register(data)


@router.get("/me", response_model=UserResponse)
async def get_me(
    service: FromDishka[IUserService],
    # TODO: потом сюда прилетит current_user: FromDishka[User]
):
    # Заглушка — потом заменим на реального пользователя
    return {"id": "00000000-0000-0000-0000-000000000000", "email": "test@test.com", "username": "test", "name": None, "created_at": "2024-01-01T00:00:00"}