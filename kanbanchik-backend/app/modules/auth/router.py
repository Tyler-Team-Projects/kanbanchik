from fastapi import APIRouter, status
from dishka.integrations.fastapi import FromDishka, inject

from app.modules.auth.service import IAuthService
from app.modules.auth.schemas import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@inject
async def login(
    data: LoginRequest,
    service: FromDishka[IAuthService] = None,
):
    tokens = await service.login(data.email_or_username, data.password)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
@inject
async def refresh(
    data: RefreshRequest,
    service: FromDishka[IAuthService] = None,
):
    tokens = await service.refresh(data.refresh_token)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def logout(
    data: RefreshRequest,
    service: FromDishka[IAuthService] = None,
):
    await service.logout(data.refresh_token)
    return