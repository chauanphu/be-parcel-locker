import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from main import app  # Assuming your FastAPI app instance is in main.py
from models.profile import Profile  # Import the Profile model
from database.session import get_db  # Import the get_db dependency
from routers.profile import router  # Import your router
from routers.profile import get_user

# Fixture to initialize the test client
client = TestClient(app)

def test_get_user_success(mock_db_session, auth_headers):
    # Mock profile data to be returned by the query
    mock_profile = Profile(user_id=1, name="John Doe", gender="Male", age=30, phone="1234567890", address="123 Street")
    mock_db_session.query().filter().first.return_value = mock_profile

    # Call the /profile/{user_id} route with a valid user_id
    response = client.get("api/v1/profile/1", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == {
        "user_id": 1,
        "name": "John Doe",
        "gender": "Male",
        "age": 30,
        "phone": "1234567890",
        "address": "123 Street"
    }

def test_get_user_not_found(client, mock_db_session, auth_headers):
    # Mock the case where the user is not found in the database
    mock_db_session.query().filter().first.return_value = None

    # Call the /profile/{user_id} route with an invalid user_id
    response = client.get("api/v1/profile/1", headers=auth_headers)
    
    assert response.status_code == 404
    assert response.json() == {"detail": "User profile not found"}

def test_update_profile(client, mock_db_session, auth_headers):
    """Test the PUT /profile/{user_id} endpoint to update profile."""
    # Mock profile data to be returned by the query
    mock_profile = Profile(user_id=1, name="John Doe", gender="Male", age=30, phone="1234567890", address="123 Street")
    mock_db_session.query().filter().first.return_value = mock_profile
    
    update_request = {
        "name": "string",
        "address": {
            "address_number": "string",
            "street": "string",
            "ward": "string",
            "district": "string"
        },
        "phone": "string",
        "gender": "Male",
        "age": 0
    }
    response = client.put("/api/v1/profile/1/update_profile", json=update_request, headers=auth_headers)
    print("response:", response.json())
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert data["message"] == "Profile updated successfully"

