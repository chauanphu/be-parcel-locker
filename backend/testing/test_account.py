import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app  # assuming your FastAPI app is in main.py
from database.session import get_db # imports for dependency overrides
from auth.utils import get_current_user
from conftest import override_get_db

client = TestClient(app)


def test_create_account(auth_headers):
    new_account = {
        "email": "user@example.com",
        "username": "user1",
        "password": "hashed_password"
    }

    response = client.post("/api/v1/account/create_account/", json=new_account, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert response.json()["username"] == "user1"

def test_delete_account_for_non_admin(auth_headers):
    response = client.delete("/api/v1/account/delete_account_for_current_user/", headers=auth_headers)
    assert response.status_code == 200
    # assert response.json() == {"Message": "Account deleted successfully"}
    assert "Message" in response.json()

# def test_delete_account_for_admin_profile(auth_headers):
#     # Here, the mocked user has the profile "Admin"
#     # app.dependency_overrides[get_current_user] = lambda: Account(user_id=1, email="admin@example.com")
    
#     response = client.delete("/api/v1/account/delete_account_for_current_user/", headers=auth_headers)
    
#     assert response.status_code == 400
#     assert response.json()["detail"] == "You cannot delete an admin profile"

# def test_delete_admin_account(auth_headers):
#     # Mock user with admin email
#     # app.dependency_overrides[get_current_user] = lambda: Account(user_id=1, email="admin@example.com")

#     response = client.delete("/api/v1/account/delete_account_for_current_user/", headers=auth_headers)
#     assert response.status_code == 400
#     assert response.json()["detail"] == "You cannot delete an admin account"
