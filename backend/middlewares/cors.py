from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

origins = [
    'http://localhost:3000'
]

def apply_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    return app