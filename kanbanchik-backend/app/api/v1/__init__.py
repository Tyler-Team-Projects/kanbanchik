from fastapi import APIRouter

from app.modules.users.router import router as users_router

router = APIRouter()
<<<<<<< HEAD
<<<<<<< HEAD
router.include_router(users_router)
=======
router.include_router(users_router, prefix="/users")
>>>>>>> d5e46f4 (feat: add first model and work schema for try start project with dishka)
=======
router.include_router(users_router)
>>>>>>> 7c2a80d (fix: worked app with dishka for users model; stable version of now)
