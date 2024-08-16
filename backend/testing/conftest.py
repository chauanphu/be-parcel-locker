# test_main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock,patch
from main import app  # Import your FastAPI app
from auth.utils import bcrypt_context, authenticate_user
from models.account import Account
from database.session import get_db
from sqlalchemy.orm import Session
from decouple import config
from passlib.context import CryptContext
ADMIN_USERNAME = config("ADMIN_USERNAME")
ADMIN_PASSWORD = config("ADMIN_PASSWORD")
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("algorithm", default="HS256")


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Mock the database session
mock_session = MagicMock()


def override_get_db():
    try:
        yield mock_session
    finally:
        pass

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db_session():
    return mock_session


# Additional tests can be added here
