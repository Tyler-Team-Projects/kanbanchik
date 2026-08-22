from fastapi import APIRouter

from app.modules.users.router import router as users_router

router = APIRouter()
router.include_router(users_router)