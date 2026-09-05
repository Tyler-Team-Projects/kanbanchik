from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dishka.integrations.fastapi import FromDishka, inject

from app.modules.auth.service import IAuthService
from app.api.schemas import CurrentUser

oauth2_scheme = HTTPBearer()


@inject
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    auth_service: FromDishka[IAuthService] = None,
) -> CurrentUser:
    """
    Возвращает данные текущего авторизованного пользователя в виде Pydantic-схемы.
    """
    token = credentials.credentials
    user_model = await auth_service.get_user_from_token(token)
    return CurrentUser.model_validate(user_model)
