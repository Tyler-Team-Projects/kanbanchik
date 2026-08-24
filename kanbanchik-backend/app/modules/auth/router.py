from fastapi import APIRouter, HTTPException, status
from dishka.integrations.fastapi import FromDishka, inject
from pydantic import BaseModel

from app.modules.auth.service import IAuthService
from app.modules.auth.schemas import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(tags=["auth"])

@router.post("/login", response_model=TokenResponse)
@inject
async def login(
        data: LoginRequest,
        service: FromDishka[IAuthService] = None,
):
    try:
        tokens = await service.login(data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return tokens

@router.post("/refresh", response_model=TokenResponse)
@inject
async def refresh(
    data: RefreshRequest,
    service: FromDishka[IAuthService] = None,
):
    try:
        tokens = await service.refresh(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def logout(
    data: RefreshRequest,
    service: FromDishka[IAuthService] = None,
):
    try:
        await service.logout(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return