import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from routers.locker import router  # Import your router and models
from fastapi import FastAPI
from main import app
from unittest.mock import MagicMock

client = TestClient(app)


# Test function for the create_locker endpoint
def test_create_locker(auth_headers):
    payload = {
        "address": "123 Test St",
        "latitude": 12.34,
        "longitude": 56.78,

    }
    response = client.post("/api/v1/locker/", json=payload , headers=auth_headers)
    assert response.status_code == 200    
 
# # Test function for the get_lockers_by_paging endpoint
# def test_get_lockers_by_paging():
#     response = client.get("api/v1/locker2/?page=1&per_page=10" ,)
#     assert response.status_code == 200
#     assert "total" in response.json()
#     assert "page" in response.json()
#     assert "per_page" in response.json()
#     assert "data" in response.json()
       
# Test function for the get_locker endpoint
def test_get_locker(mock_db_session,auth_headers):
    # Arrange: Configure the mock to return a valid locker object
    mock_locker = MagicMock()
    mock_locker.locker_id = 2
    mock_locker.address = "123 Test St"
    mock_locker.latitude = 12.34
    mock_locker.longitude = 56.78
    mock_locker.locker_status = "Active"

    # Mock the query and filtering logic
    mock_db_session.query().filter().first.return_value = mock_locker

    response = client.get(f"/api/v1/locker/2", headers=auth_headers)
    assert response.status_code == 200
    response_data = response.json()
    print("response_data:", response_data)
    # Assert: Check that the correct values are returned in the response
    assert response_data["locker_id"] == 2
    assert response_data["address"] == "123 Test St"
    assert response_data["locker_status"] == "Active"
    
# # Test function for the get_cells_by_paging endpoint
# def test_get_cells_by_paging(auth_headers,mock_db_session):
#     # Arrange: Set up the mock lockers and cells
#     mock_locker = {
#         "locker_id": 1,
#         "address": "123 Test St",
#         "latitude": 12.34,
#         "longitude": 56.78,
#         "locker_status": "Active",
#         "date_created": "2024-09-10",  # Example date
#         "cells": [
#             {
#                 "cell_id": 1,
#                 "occupied": False,
#                 "size": "Medium"
#             }
#         ]
#     }

#     # Mock the database query results
#     mock_db_session.query().count.return_value = 1  # One locker
#     mock_db_session.query().offset().limit().all.return_value = [mock_locker]
#     mock_db_session.query().filter().all.return_value = mock_locker["cells"]  # Cells for the locker
    
#     # Act: Call the GET method to retrieve lockers by paging
#     response = client.get("/api/v1/locker2/?page=1&per_page=10", headers=auth_headers)
#     # Assert: Check the response status code and structure
#     assert response.status_code == 200
#     response_data = response.json()
#     print("Response data:", response_data)

    
#     # Verify pagination info
#     assert "total" in response_data
#     assert "page" in response_data
#     assert "per_page" in response_data
#     assert "total_pages" in response_data
#     assert "data" in response_data
    
#     # Verify lockers data
#     lockers = response_data["data"]
    
#     assert len(lockers) == 1  # Only one locker in the mocked response
#     locker = lockers[0]

#      # Check if locker has the expected keys
#     assert "locker_id" in locker
#     assert "address" in locker
#     assert "latitude" in locker
#     assert "longitude" in locker
#     assert "locker_status" in locker
#     assert "date_created" in locker
#     assert "cells" in locker


#     # Verify locker details
#     assert locker["locker_id"] == mock_locker["locker_id"]
#     assert locker["address"] == mock_locker["address"]
#     assert locker["latitude"] == mock_locker["latitude"]
#     assert locker["longitude"] == mock_locker["longitude"]
#     assert locker["locker_status"] == mock_locker["locker_status"]
#     assert locker["date_created"] == mock_locker["date_created"]

#     # Verify cells data inside the locker
#     cells = locker["cells"]
#     assert len(cells) == 1  # Only one cell in the mocked response
#     cell = cells[0]

#     assert cell["cell_id"] == mock_locker["cells"][0]["cell_id"]
#     assert cell["occupied"] == mock_locker["cells"][0]["occupied"]
#     assert cell["size"] == mock_locker["cells"][0]["size"]

# Test function for the create_cell endpoint


# # Test function for the update_locker endpoint
# def test_update_locker():
#     locker_id = 1  # Assuming locker_id = 1 exists in the test database
#     payload = {
#         "address": "456 Updated St"
#     }
#     response = client.put(f"/api/v1/locker/{locker_id}", json=payload)
#     assert response.status_code == 200
#     assert "Message" in response.json()

# Test function for the delete_locker endpoint
def test_delete_locker(auth_headers):
    locker_id = 1  # Assuming locker_id = 1 exists in the test database
    response = client.delete(f"/api/v1/locker/{locker_id}", headers= auth_headers)
    assert response.status_code == 200
    assert "Message" in response.json()


# Test function for the get_density endpoint
def test_get_density(auth_headers):
    locker_id = 2  # Assuming locker_id = 1 exists in the test database
    response = client.get(f"/api/v1/locker/{locker_id}/size/S/density", headers=auth_headers)
    assert response.status_code == 200
    assert "density_status" in response.json()
