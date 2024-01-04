from fastapi import APIRouter
from auth.router import router as auth_router
from .user import router as student_router
from .locker import router as locker_router
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(student_router)
api_router.include_router(locker_router)