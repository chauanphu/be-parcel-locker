import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from routers.location import router, location_data_list  # Import your router and models
from fastapi import FastAPI
from typing import List

app = FastAPI()
app.include_router(router)

client = TestClient(app)
FIXED_TIMESTAMP = "2024-08-13T08:18:09"

@pytest.fixture(autouse=True)
def clear_data():
    """Clear the location_data_list before each test."""
    location_data_list.clear()
    
@pytest.fixture
def mock_data() -> List[dict]:
    return [
        {
            "latitude": 12.34,
            "longitude": 56.78,
            "timestamp": FIXED_TIMESTAMP,
            "altitude": 100.0,
            "speed": 50.0,
            "accuracy": 10.0
        }
    ]

def test_receive_location_data(client, mock_data):
    # Test POST endpoint
    data = mock_data[0]
    response = client.post("/api/v1/location/", json=data)
    assert response.status_code == 200
    response_data = response.json()
    # Compare the fixed timestamp
    assert response_data['timestamp'] == data['timestamp']
    # Remove timestamp for comparison
    response_data.pop('timestamp', None)
    data_copy = data.copy()
    data_copy.pop('timestamp', None)
    assert response_data == data_copy

def test_get_location_data(client, mock_data):
    # Test GET endpoint
    data = mock_data[0]
    client.post("/api/v1/location/", json=data)
    response = client.get("/api/v1/location/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0] == data
    
def test_websocket(client):
    # Test WebSocket endpoint
    with client.websocket_connect("ws://localhost:8000/api/v1/location/ws") as websocket:
        websocket.send_json({
            "latitude": 34.56,
            "longitude": 78.90,
            "timestamp": FIXED_TIMESTAMP,
            "altitude": 200.0,
            "speed": 60.0,
            "accuracy": 5.0
        })
        response = websocket.receive_json()
        assert response["status"] == "received"
        assert response["data"]["latitude"] == 34.56
        assert response["data"]["longitude"] == 78.90

        # Test error handling
        websocket.send_json({
            "latitude": "invalid",  # Invalid data
            "longitude": 78.90,
            "timestamp": FIXED_TIMESTAMP
        })
        response = websocket.receive_json()
        assert response["status"] == "error"
        error_message = response["message"]
        assert "validation error" in error_message
        assert "latitude" in error_message
        assert "Input should be a valid number" in error_message
