import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app  # Assuming your FastAPI app instance is in main.py
from models.profile import Profile  # Import the Profile model
from database.session import get_db  # Import the get_db dependency
from routers.profile import router  # Import your router

# Fixture to initialize the test client
client = TestClient(app)

# Test data for creating a profile
test_user_id = 1
test_profile_data = {
    "user_id": test_user_id,
    "name": "John Doe",
    "gender": "Male",
    "age": 30,
    "phone": "3333333",
    "address": "123 Ho Tung Mau St, District/City 1"
}

@pytest.fixture(autouse=True)
def setup_db():
    """Setup the database and teardown after each test."""
    # Assuming you have a function to get a test DB session
    # Replace `get_test_db` with your actual test DB session fixture
    db = get_db()
    profile = Profile(**test_profile_data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    yield db  # Test happens here
    db.query(Profile).delete()
    db.commit()

def test_get_user():
    """Test the GET /profile/{user_id} endpoint."""
    response = client.get(f"/profile/{test_user_id}")
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["user_id"] == test_user_id
    assert user_data["name"] == test_profile_data["name"]
    assert user_data["gender"] == test_profile_data["gender"]
    assert user_data["age"] == test_profile_data["age"]
    assert user_data["phone"] == test_profile_data["phone"]
    assert user_data["address"] == test_profile_data["address"]

def test_get_paging_users():
    """Test the GET /profile/ endpoint with pagination."""
    response = client.get("/profile/?page=1&per_page=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "total_pages" in data
    assert "data" in data
    assert len(data["data"]) == 1  # We only added one profile in the setup

def test_update_user():
    """Test the PUT /profile/{user_id} endpoint."""
    new_data = {
        "name": "Jane Doe",
        "gender": "Female",
        "age": 28,
        "phone": "987654321",
        "address": {
            "address_number": "456",
            "street": "Second St",
            "ward": "2",
            "district": "District/City 2"
        }
    }
    response = client.put(f"/profile/{test_user_id}", json=new_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["name"] == new_data["name"]
    assert updated_user["gender"] == new_data["gender"]
    assert updated_user["age"] == new_data["age"]
    assert updated_user["phone"] == new_data["phone"]
    assert updated_user["address"] == "456, Second St Street, 2 Ward, District/City 2"

def test_update_profile():
    """Test the PUT /profile/{user_id} endpoint to update profile."""
    update_request = {
        "name": "Updated Name",
        "gender": "Female",
        "age": 25,
        "phone": "999999999",
        "address": "Updated Address"
    }
    response = client.put(f"/profile/{test_user_id}", json=update_request)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Profile updated successfully"
    assert data["profile"]["name"] == update_request["name"]
    assert data["profile"]["gender"] == update_request["gender"]
    assert data["profile"]["age"] == update_request["age"]
    assert data["profile"]["phone"] == update_request["phone"]
    assert data["profile"]["address"] == update_request["address"]
