# test_main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app  # Import your FastAPI app
from database.session import get_db
from fastapi import APIRouter

# Mock the database session
mock_session = MagicMock()

# Override the database dependency with the test database session
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
