from fastapi import FastAPI
from middlewares.cors import apply_cors_middleware
from routers import api_router
import database.setup

def create_app() -> FastAPI:
    app = FastAPI()

    app = apply_cors_middleware(app)
    app.include_router(api_router)
    
    return app