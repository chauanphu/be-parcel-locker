from fastapi import FastAPI
from middlewares.cors import apply_cors_middleware
from database import setup
from states.shipment import *
from vrp_solver import *
from routers import api_router
from routers import websocket_router

def create_app() -> FastAPI:
    app = FastAPI(docs_url="/api", redoc_url=None, openapi_url="/api/openapi.json")
    setup.create_roles()
    setup.create_default_admin()
    app = apply_cors_middleware(app)
    app.include_router(api_router)
    app.include_router(websocket_router)
    return app