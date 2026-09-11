from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dishka import AsyncContainer
from redis.asyncio import Redis
from dishka.integrations.fastapi import setup_dishka
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.base import engine
from app.core.di import container as prod_container
from app.api.v1 import router as api_v1_router
from app.core.exceptions import BaseDomainException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan-контекст."""
    async with app.state.dishka_container() as req:
        await req.get(Redis)
    yield
    await engine.dispose()


def create_app(container: AsyncContainer | None = None) -> FastAPI:
    """
    Фабрика приложения.

    В продакшене: `app = create_app()` — используется глобальный контейнер из `app.core.di`.
    В тестах:     `app = create_app(test_container)` — контейнер передаётся явно.
    """
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Регистрируем обработчики исключений
    register_exception_handlers(app)

    # Роутеры
    app.include_router(api_v1_router, prefix="/api/v1")

    register_health_endpoints(app)

    setup_dishka(container or prod_container, app)

    return app


def register_health_endpoints(app: FastAPI) -> None:
    @app.get("/")
    async def root() -> dict:
        return {"message": "Kanbanchik API", "version": "0.1.0", "status": "running"}

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy", "service": "kanbanchik-backend"}

    @app.get("/ping")
    async def ping() -> dict:
        return {"pong": True}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseDomainException)
    async def domain_exception_handler(request: Request, exc: BaseDomainException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers or {},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        if "duplicate key" in str(exc).lower():
            detail = "Запись с таким значением уже существует"
            if "email" in str(exc).lower():
                detail = "Пользователь с таким email уже существует"
            elif "username" in str(exc).lower():
                detail = "Пользователь с таким username уже существует"
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": detail})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Внутренняя ошибка сервера"},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Внутренняя ошибка сервера"},
        )


# Точка входа для uvicorn: `uvicorn app.main:app`
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)