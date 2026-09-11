from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from jose import ExpiredSignatureError, JWTError, jwt
from uuid_extension import uuid7
from app.core.config import settings
from app.core.exceptions import (
    InternalServerErrorException,
    InvalidTokenException,
    TokenExpiredException,
)

_hasher = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хешу.
    """
    try:
        return _hasher.verify(hashed_password, plain_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Генерирует хеш пароля с использованием Argon2id.
    """
    return _hasher.hash(password)


def create_access_token(
    data: dict,
    secret_key: str,
    expires_delta: timedelta,
    algorithm: str = "HS256",
) -> str:
    """
    Создаёт JWT access token.
    """
    if expires_delta is None:
        raise InternalServerErrorException("Для токена доступа обязательно требуется время жизни")

    now = datetime.now(timezone.utc)
    payload = data.copy()
    payload.update({
        "exp": now + expires_delta,
        "iat": now,
    })
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(
    data: dict,
    secret_key: str,
    expires_delta: timedelta,
    algorithm: str = "HS256",
) -> str:
    """
    Создаёт JWT refresh token с уникальным идентификатором jti.
    """
    if expires_delta is None:
        raise InternalServerErrorException("Для токена обновления обязательно требуется время жизни")
    if "jti" not in data:
        raise InternalServerErrorException("Для refresh-токена обязательно поле 'jti'")
    now = datetime.now(timezone.utc)
    payload = data.copy()
    payload.update({
        "exp": now + expires_delta,
        "iat": now,
    })
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_token(token: str, secret_key: str, algorithm: str = settings.jwt_algorithm) -> dict:
    """
    Декодирует и валидирует JWT токен.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except ExpiredSignatureError:
        raise TokenExpiredException()
    except JWTError:
        raise InvalidTokenException()