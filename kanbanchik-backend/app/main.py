from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Создаём приложение
app = FastAPI(
    title="Kanbanchik API",
    description="Сервис для управления проектами и задачами",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict:
    """Корневой эндпоинт."""
    return {
        "message": "Kanbanchik API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health() -> dict:
    """Проверка работоспособности."""
    return {
        "status": "healthy",
        "service": "kanbanchik-backend",
    }


@app.get("/ping")
async def ping() -> dict:
    """Простой ping."""
    return {"pong": True}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )