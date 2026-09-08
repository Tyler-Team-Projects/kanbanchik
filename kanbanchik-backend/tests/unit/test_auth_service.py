import pytest
from uuid import uuid4
from datetime import timedelta, datetime, timezone
from jose import jwt
import time_machine  # Для заморозки времени и тестирования протухания токенов

from app.core.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    RefreshTokenNotFoundException,
    UserNotFoundException,
    UserInactiveException,
)
from app.core.security import get_password_hash, create_access_token, create_refresh_token, decode_token
from app.modules.auth.service import AuthService
from app.modules.auth.repository import IRefreshTokenRepository
from app.modules.auth.schemas import RefreshTokenData
from app.modules.users.repository import IUserRepository
from app.modules.users.models import User
from app.core.config import Settings
from tests.factories import UserFactory
from uuid_extension import uuid7


# ---------- Fake репозитории ----------
class FakeUserRepository(IUserRepository):
    def __init__(self):
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}
        self._username_index: dict[str, str] = {}

    async def get_by_id(self, user_id):
        key = str(user_id)
        return self._users.get(key)

    async def get_by_email_or_username(self, value: str) -> User | None:
        user_id = self._email_index.get(value)
        if user_id:
            return self._users.get(user_id)
        user_id = self._username_index.get(value)
        if user_id:
            return self._users.get(user_id)
        return None

    async def create(self, user: User) -> User:
        self._users[str(user.id)] = user
        self._email_index[user.email] = str(user.id)
        self._username_index[user.username] = str(user.id)
        return user


class FakeRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self):
        self._tokens: dict[str, dict] = {}

    async def save(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        # Используем детерминированное время, которое можно заморозить в тестах
        now = datetime.now(timezone.utc)
        self._tokens[jti] = {
            "user_id": user_id,
            "expires_at": now + timedelta(seconds=ttl_seconds),
            "created_at": now,
        }

    async def get(self, jti: str) -> RefreshTokenData | None:
        data = self._tokens.get(jti)
        if not data:
            return None
        return RefreshTokenData(**data)

    async def delete(self, jti: str) -> None:
        self._tokens.pop(jti, None)

    async def exists(self, jti: str) -> bool:
        return jti in self._tokens


# ---------- Фикстуры ----------
@pytest.fixture
def test_settings():
    return Settings(
        secret_key="test-secret-key",
        jwt_algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )


@pytest.fixture
def fake_user_repo():
    return FakeUserRepository()


@pytest.fixture
def fake_refresh_repo():
    return FakeRefreshTokenRepository()


@pytest.fixture
def auth_service(fake_user_repo, fake_refresh_repo, test_settings):
    return AuthService(
        user_repo=fake_user_repo,
        refresh_repo=fake_refresh_repo,
        settings=test_settings,
    )


# ---------- Тесты ----------
@pytest.mark.asyncio
async def test_login_success_returns_tokens(auth_service, fake_user_repo, fake_refresh_repo, test_settings):
    password = "secure123"
    password_hash = get_password_hash(password)
    user = UserFactory(password_hash=password_hash)
    await fake_user_repo.create(user)

    tokens = await auth_service.login(user.email, password)

    assert "access_token" in tokens
    assert "refresh_token" in tokens
    payload = decode_token(tokens["refresh_token"], test_settings.secret_key, test_settings.jwt_algorithm)
    jti = payload.get("jti")
    assert jti is not None
    token_data = await fake_refresh_repo.get(jti)
    assert token_data is not None
    assert token_data.user_id == str(user.id)


@pytest.mark.asyncio
async def test_login_wrong_password_raises_invalid_credentials(auth_service, fake_user_repo):
    user = UserFactory(password_hash=get_password_hash("correct"))
    await fake_user_repo.create(user)

    with pytest.raises(InvalidCredentialsException):
        await auth_service.login(user.email, "wrong")


@pytest.mark.asyncio
async def test_login_nonexistent_user_raises_invalid_credentials(auth_service):
    with pytest.raises(InvalidCredentialsException):
        await auth_service.login("unknown@example.com", "pass")


@pytest.mark.asyncio
async def test_refresh_success(auth_service, fake_refresh_repo, test_settings):
    user_id = str(uuid4())
    jti = "test-jti-1"
    refresh_ttl = test_settings.refresh_token_expire_days * 24 * 3600
    await fake_refresh_repo.save(jti, user_id, refresh_ttl)

    refresh_token = create_refresh_token(
        data={"sub": user_id, "jti": jti},
        secret_key=test_settings.secret_key,
        expires_delta=timedelta(days=test_settings.refresh_token_expire_days),
        algorithm=test_settings.jwt_algorithm,
    )

    new_tokens = await auth_service.refresh(refresh_token)

    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    old = await fake_refresh_repo.get(jti)
    assert old is None
    new_payload = decode_token(new_tokens["refresh_token"], test_settings.secret_key, test_settings.jwt_algorithm)
    new_jti = new_payload.get("jti")
    assert new_jti is not None
    new_data = await fake_refresh_repo.get(new_jti)
    assert new_data is not None


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_raises(auth_service):
    with pytest.raises(InvalidTokenException):
        await auth_service.refresh("invalid-token")


@pytest.mark.asyncio
async def test_refresh_with_missing_jti_raises(auth_service, test_settings):
    payload = {"sub": "some-user"}
    token = jwt.encode(payload, test_settings.secret_key, algorithm=test_settings.jwt_algorithm)
    with pytest.raises(InvalidTokenException):
        await auth_service.refresh(token)


@pytest.mark.asyncio
async def test_refresh_with_non_existing_jti_raises(auth_service, test_settings):
    jti = "non-existing"
    token = create_refresh_token(
        data={"sub": "user", "jti": jti},
        secret_key=test_settings.secret_key,
        expires_delta=timedelta(days=1),
        algorithm=test_settings.jwt_algorithm,
    )
    with pytest.raises(RefreshTokenNotFoundException):
        await auth_service.refresh(token)


@pytest.mark.asyncio
async def test_logout_deletes_token(auth_service, fake_refresh_repo, test_settings):
    user_id = str(uuid4())
    jti = "logout-jti"
    await fake_refresh_repo.save(jti, user_id, 3600)
    token = create_refresh_token(
        data={"sub": user_id, "jti": jti},
        secret_key=test_settings.secret_key,
        expires_delta=timedelta(days=1),
        algorithm=test_settings.jwt_algorithm,
    )

    await auth_service.logout(token)

    assert await fake_refresh_repo.get(jti) is None


@pytest.mark.asyncio
async def test_logout_invalid_token_raises(auth_service):
    with pytest.raises(InvalidTokenException):
        await auth_service.logout("invalid")


@pytest.mark.asyncio
async def test_get_user_from_token_success(auth_service, fake_user_repo, test_settings):
    user = UserFactory()
    await fake_user_repo.create(user)
    token = create_access_token(
        data={"sub": str(user.id)},
        secret_key=test_settings.secret_key,
        expires_delta=timedelta(minutes=15),
        algorithm=test_settings.jwt_algorithm,
    )

    retrieved = await auth_service.get_user_from_token(token)
    assert retrieved.id == user.id
    assert retrieved.email == user.email


@pytest.mark.asyncio
async def test_get_user_from_token_inactive_user_raises(auth_service, fake_user_repo, test_settings):
    user = UserFactory(is_active=False)
    await fake_user_repo.create(user)
    token = create_access_token(
        data={"sub": str(user.id)},
        secret_key=test_settings.secret_key,
        expires_delta=timedelta(minutes=15),
        algorithm=test_settings.jwt_algorithm,
    )
    with pytest.raises(UserInactiveException):
        await auth_service.get_user_from_token(token)


@pytest.mark.asyncio
async def test_get_user_from_token_deleted_user_raises(auth_service, test_settings):
    non_existent_uuid = str(uuid7())
    token = create_access_token(
        data={"sub": non_existent_uuid},
        secret_key=test_settings.secret_key,
        expires_delta=timedelta(minutes=15),
        algorithm=test_settings.jwt_algorithm,
    )
    with pytest.raises(UserNotFoundException):
        await auth_service.get_user_from_token(token)


@pytest.mark.asyncio
async def test_get_user_from_token_expired_raises(auth_service, fake_user_repo, test_settings):
    """Новый тест: Проверяет, что протухший Access-токен вызывает исключение."""
    user = UserFactory()
    await fake_user_repo.create(user)

    # Фиксируем начальную точку времени
    initial_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    with time_machine.travel(initial_time):
        token = create_access_token(
            data={"sub": str(user.id)},
            secret_key=test_settings.secret_key,
            expires_delta=timedelta(minutes=15),  # Токен активен до 12:15
            algorithm=test_settings.jwt_algorithm,
        )

    # Перемещаемся в будущее на 16 минут (время 12:16) — токен уже протух
    with time_machine.travel(initial_time + timedelta(minutes=16)):
        with pytest.raises(InvalidTokenException):
            await auth_service.get_user_from_token(token)
