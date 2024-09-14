from fastapi import FastAPI
from middlewares.cors import apply_cors_middleware
from routers import api_router
from database import setup
from utils.mqtt import MQTTClient
def create_app() -> FastAPI:
    app = FastAPI()
    setup.create_default_admin()
    app = apply_cors_middleware(app)
    app.include_router(api_router)
    
    return app