from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dishka.integrations.fastapi import setup_dishka

from app.core.config import settings
from app.core.redis import init_redis, close_redis
from app.db.base import engine
from app.core.di import container
from app.api.v1 import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan-контекст."""
    # Startup
    await init_redis()

    yield

    # Shutdown
    await close_redis()
    await engine.dispose()


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

app.include_router(api_v1_router, prefix="/api/v1")
# Интеграция Dishka
setup_dishka(container, app)


@app.get("/")
async def root() -> dict:
    return {
        "message": "Kanbanchik API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "kanbanchik-backend",
    }


@app.get("/ping")
async def ping() -> dict:
    return {"pong": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )