import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from routers.locker import router,router2  # Import your router and models
from fastapi import FastAPI
from typing import List
from conftest import mock_db_session, client
from routers.locker import router, router2  # Ensure correct import path
from decouple import config
from passlib.context import CryptContext
ADMIN_USERNAME = config("ADMIN_USERNAME")
ADMIN_PASSWORD = config("ADMIN_PASSWORD")
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("algorithm", default="HS256")


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
app = FastAPI()
app.include_router(router)
app.include_router(router2)

    
def test_create_locker(client, mock_db_session):
    # Mock the behavior of the database session for creating a locker
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.return_value = None
    response = client.post(
        "/api/v1/locker/",
        json={
            "address": "123 Test St",
            "latitude": 12.34,
            "longitude": 56.78,
            "locker_status": "Active"
        },
        headers={"Authorization": f"Bearer"} # Authentication credentials
    )
                
    
    assert response.status_code == 200
    assert response.json() == 1  # Assuming the response is the locker ID
    
    # Verify that add, commit, and refresh methods were called
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()

