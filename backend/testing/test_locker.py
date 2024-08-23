import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from routers.locker import router  # Import your router and models
from fastapi import FastAPI
from main import app


client = TestClient(app)


# Test function for the get_lockers_by_paging endpoint
def test_get_lockers_by_paging():
    response = client.get("api/v1/locker2/?page=1&per_page=10" ,)
    assert response.status_code == 200
    assert "total" in response.json()
    assert "page" in response.json()
    assert "per_page" in response.json()
    assert "data" in response.json()
    
# # Test function for the get_locker endpoint
# def test_get_locker(auth_headers):
#     response = client.get("/api/v1/locker/2", headers= auth_headers)
#     print("auther:", auth_headers)
#     print("response:", response)
#     assert response.status_code == 200
#     assert "locker_id" in response.json()
#     assert "address" in response.json()

# # Test function for the get_cells_by_paging endpoint
# def test_get_cells_by_paging():
#     response = client.get("/api/v1/locker/?page=1&per_page=10")
#     assert response.status_code == 200
#     assert "total" in response.json()
#     assert "page" in response.json()
#     assert "data" in response.json()

# # Test function for the create_locker endpoint
# def test_create_locker():
#     payload = {
#         "address": "123 Test St",
#         "latitude": 12.34,
#         "longitude": 56.78,
#         "locker_status": "Active"
#     }
#     response = client.post("/api/v1/locker/", json=payload)
#     assert response.status_code == 200
#     assert isinstance(response.json(), int)

# # Test function for the create_cell endpoint
# def test_create_cell():
#     locker_id = 1  # Assuming locker_id = 1 exists in the test database
#     payload = {
#         "size": "M"
#     }
#     response = client.post(f"/api/v1/locker/1/cell", json=payload)
#     assert response.status_code == 200
#     assert isinstance(response.json(), str)  # UUID as a string

# # Test function for the update_locker endpoint
# def test_update_locker():
#     locker_id = 1  # Assuming locker_id = 1 exists in the test database
#     payload = {
#         "address": "456 Updated St"
#     }
#     response = client.put(f"/api/v1/locker/{locker_id}", json=payload)
#     assert response.status_code == 200
#     assert "Message" in response.json()

# # Test function for the delete_locker endpoint
# def test_delete_locker():
#     locker_id = 1  # Assuming locker_id = 1 exists in the test database
#     response = client.delete(f"/api/v1/locker/{locker_id}")
#     assert response.status_code == 200
#     assert "Message" in response.json()

# # # Test function for the update_cell_to_false (locker_id) endpoint
# # def test_update_cell_to_false_locker():
# #     locker_id = 1  # Assuming locker_id = 1 exists in the test database
# #     response = client.put(f"/locker/{locker_id}/cell")
# #     assert response.status_code == 200
# #     assert "Message" in response.json()

# # # Test function for the update_cell_to_false (order_id) sending endpoint
# # def test_update_sending_cell_to_false():
# #     order_id = 1  # Assuming order_id = 1 exists in the test database
# #     response = client.put(f"/locker/{order_id}/update sending cell occupied to False")
# #     assert response.status_code == 200
# #     assert "Message" in response.json()

# # # Test function for the update_cell_to_false (order_id) receiving endpoint
# # def test_update_receiving_cell_to_false():
# #     order_id = 1  # Assuming order_id = 1 exists in the test database
# #     response = client.put(f"/locker/{order_id}/update receiving cell occupied to False")
# #     assert response.status_code == 200
# #     assert "Message" in response.json()

# # Test function for the get_density endpoint
# def test_get_density():
#     locker_id = 1  # Assuming locker_id = 1 exists in the test database
#     response = client.get(f"api/v1/locker/{locker_id}/density")
#     assert response.status_code == 200
#     assert "density_status" in response.json()
