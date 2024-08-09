from fastapi import APIRouter
from auth.router import router as auth_router
from .user import router as student_router
from .user import router2 as student_router2
from .user import public_router as public_router
from .locker import router as locker_router
from .locker import router2 as locker_router2
from .order import router as order_router
from .parcel import router as parcel_router
from .location import router as location_router


api_router = APIRouter(prefix="/api/v1")



api_router.include_router(auth_router)
api_router.include_router(student_router)
api_router.include_router(student_router2)
api_router.include_router(public_router)
api_router.include_router(locker_router2)
api_router.include_router(locker_router)
api_router.include_router(order_router)
api_router.include_router(parcel_router)
api_router.include_router(location_router)