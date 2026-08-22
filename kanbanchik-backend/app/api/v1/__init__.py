from fastapi import APIRouter
from app.modules.users.router import router as users_router
from app.modules.workspaces.router import router as workspaces_router

router = APIRouter()
router.include_router(users_router)
router.include_router(workspaces_router)
