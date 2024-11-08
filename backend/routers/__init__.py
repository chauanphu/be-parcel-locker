from fastapi import APIRouter
from auth.router import router as auth_router

from .locker import router as locker_router
from .order import router as order_router
from .parcel import router as parcel_router
from .location import router as location_router

from .account import router as account_router

from .profile import router as profile_router
from .recipient import router as recipent_router
from .file import router as file_router
api_router = APIRouter(prefix="/api/v1")



api_router.include_router(auth_router)

api_router.include_router(locker_router)

api_router.include_router(order_router)
api_router.include_router(parcel_router)
api_router.include_router(location_router)

api_router.include_router(account_router)

api_router.include_router(profile_router)
api_router.include_router(recipent_router)
api_router.include_router(file_router)
# api_router.include_router(shipper_router)


