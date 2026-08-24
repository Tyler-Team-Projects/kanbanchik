from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from jose import ExpiredSignatureError, JWTError, jwt
from uuid_extension import uuid7
from app.core.config import settings

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


def _ensure_jti(data: dict) -> dict:
    """
    Гарантирует наличие поля 'jti' в payload. Если отсутствует — генерирует uuid7.

    Args:
        data: Словарь с данными для токена.

    Returns:
        Словарь с гарантированным ключом 'jti'.
    """
    if "jti" not in data:
        data["jti"] = str(uuid7())
    return data


def create_access_token(
    data: dict,
    secret_key: str,
    expires_delta: settings.access_token_expire_minutes,
    algorithm: settings.jwt_algorithm,
) -> str:
    """
    Создаёт JWT access token.
    """
    if expires_delta is None:
        raise ValueError("Для токена доступа обязательно требуется время жизни")

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
    expires_delta: settings.refresh_token_expire_days,
    algorithm: str = settings.jwt_algorithm,
) -> str:
    """
    Создаёт JWT refresh token с уникальным идентификатором jti.
    """
    if expires_delta is None:
        raise ValueError("Для токена доступа обязательно требуется время жизни")

    now = datetime.now(timezone.utc)
    payload = data.copy()
    payload.update({
        "exp": now + expires_delta,
        "iat": now,
        "jti": str(uuid7()),
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
        raise ValueError("Время жизни токена истекло")
    except JWTError as e:
        raise ValueError(f"Неверный токен: {str(e)}")