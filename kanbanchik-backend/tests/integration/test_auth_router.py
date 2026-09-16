import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import UserFactory


TEST_PASSWORD = "test_password"


@pytest.fixture
async def seeded_user(db_transaction):
    """
    Кладёт в тестовую БД пользователя с известным email/username/паролем.
    Использует ту же транзакцию, что и get_session внутри запросов (через ContextVar).
    """
    session = AsyncSession(
        bind=db_transaction,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    UserFactory._session = session
    try:
        user = await UserFactory.create(
            email="integration@kanbanchik.ru",
            username="integration_user",
        )
        yield user
    finally:
        UserFactory._session = None
        await session.close()


class TestAuthFlow:
    """Интеграционные тесты auth-цикла через реальные HTTP + БД + Redis."""

    async def test_health_endpoint(self, async_client: AsyncClient):
        """Smoke-тест: приложение поднимается и отвечает."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    async def test_protected_endpoint_without_token(self, async_client: AsyncClient):
        """Без токена /users/me должен вернуть 403 (HTTPBearer auto_error)."""
        response = await async_client.get("/api/v1/users/me")
        assert response.status_code in (401, 403)

    async def test_login_wrong_password(
        self, async_client: AsyncClient, seeded_user, _clear_redis
    ):
        """Неверный пароль → 401 с понятным сообщением."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email_or_username": seeded_user.email, "password": "wrong"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_login_without_password(
        self, async_client: AsyncClient, seeded_user, _clear_redis
    ):
        """Неверный пароль → 401 с понятным сообщением."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email_or_username": seeded_user.email, "password": ""},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_login_for_unregistered_user(
        self, async_client: AsyncClient, seeded_user, _clear_redis
    ):
        """Неверный логин/почта или пароль → 401 с понятным сообщением."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email_or_username": "integration2@kanbanchik.ru", "password": TEST_PASSWORD},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_full_auth_cycle(
        self, async_client: AsyncClient, seeded_user, _clear_redis
    ):
        """
        Полный цикл:
        логин → доступ к защищённому эндпоинту → refresh (ротация) →
        повторное использование старого refresh-токена → logout → отказ после logout.
        """
        # --- 1. Логин ---
        login_resp = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email_or_username": seeded_user.email,
                "password": TEST_PASSWORD,
            },
        )
        assert login_resp.status_code == 200, login_resp.text
        tokens = login_resp.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_1 = tokens["access_token"]
        refresh_1 = tokens["refresh_token"]

        # --- 2. Доступ к защищённому эндпоинту ---
        me_resp = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_1}"},
        )
        assert me_resp.status_code == 200, me_resp.text
        me = me_resp.json()
        assert me["email"] == seeded_user.email
        assert me["username"] == seeded_user.username

        # --- 3. Refresh: должна произойти ротация ---
        refresh_resp = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_1},
        )
        assert refresh_resp.status_code == 200, refresh_resp.text
        new_tokens = refresh_resp.json()
        assert new_tokens["refresh_token"] != refresh_1
        refresh_2 = new_tokens["refresh_token"]

        # --- 4. Access: новый токен работает ---
        access_2 = new_tokens["access_token"]
        me_after_refresh = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_2}"},
        )
        assert me_after_refresh.status_code == 200

        # --- 5. Старый refresh-токен инвалидирован (ротация) ---
        replay_resp = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_1},
        )
        assert replay_resp.status_code == 401, replay_resp.text

        # --- 6. Logout ---
        logout_resp = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_2},
        )
        assert logout_resp.status_code == 204

        # --- 7. После logout новый refresh-токен тоже не работает ---
        after_logout = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_2},
        )
        assert after_logout.status_code == 401, after_logout.text

        # --- 8. Access stateless: после logout он ещё валиден до exp ---
        me_after_logout = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_2}"},
        )
        assert me_after_logout.status_code == 200

    async def test_refresh_with_garbage_token(
        self, async_client: AsyncClient, _clear_redis
    ):
        """Мусорный refresh-токен → 401."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not-a-jwt-at-all"},
        )
        assert response.status_code == 401