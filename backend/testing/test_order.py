import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from routers.order import router  # Import your router and models
from fastapi import FastAPI
from typing import List

app = FastAPI()
app.include_router(router)

client = TestClient(app)

db_list = []