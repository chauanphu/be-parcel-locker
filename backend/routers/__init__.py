from fastapi import APIRouter
from auth.router import router as auth_router

from .locker import router as locker_router
from .locker import router2 as locker_router2
from .order import router as order_router
from .parcel import router as parcel_router
from .location import router as location_router

from .account import router as account_router
from .account import router2 as account_router2
from .account import public_router as a_public_router

from .profile import router as profile_router
from .recipient import router as recipent_router

from .test_db_otp_linkedlist import router as router_linkedlist
from .test_db_otp_hash import router as router_hashlist
api_router = APIRouter(prefix="/api/v1")



api_router.include_router(auth_router)

api_router.include_router(locker_router2)
api_router.include_router(locker_router)

api_router.include_router(order_router)
api_router.include_router(parcel_router)
api_router.include_router(location_router)

api_router.include_router(account_router)
api_router.include_router(account_router2)
api_router.include_router(a_public_router)

api_router.include_router(profile_router)
api_router.include_router(recipent_router)

api_router.include_router(router_linkedlist)
api_router.include_router(router_hashlist)
