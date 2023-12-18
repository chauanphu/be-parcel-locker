from fastapi import FastAPI
from middlewares.cors import apply_cors_middleware
from database import Base, engine
from routers import api_router

def create_app() -> FastAPI:
    app = FastAPI()
    Base.metadata.create_all(bind=engine)

    app = apply_cors_middleware(app)
    app.include_router(api_router)
    
    return app