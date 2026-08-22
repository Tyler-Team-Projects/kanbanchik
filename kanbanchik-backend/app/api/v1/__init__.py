from fastapi import APIRouter

from app.modules.users.router import router as users_router
from app.modules.boards.router import router as boards_router

router = APIRouter()
router.include_router(users_router)
router.include_router(boards_router)