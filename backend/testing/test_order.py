import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from routers.order import router  # Import your router and models
from fastapi import FastAPI
from typing import List
from unittest.mock import MagicMock, patch
from models.account import Account

app = FastAPI()
app.include_router(router)

client = TestClient(app)

# Test successful order creation
@patch('order.get_db')
@patch('order.get_current_user')
@patch('order.find_available_cell')
@patch('order.change_cell_occupied')
@patch('order.get_user_id_by_recipient_info')

def test_create_order_success(mock_get_user, mock_find_cell, mock_change_cell, mock_get_user_id, mock_get_db, mock_current_user, mock_db_session, auth_headers):
    # Mock database session
    mock_get_db.return_value = mock_db_session
    mock_get_user.return_value = mock_current_user

    # Mock function returns
    mock_find_cell.side_effect = [
        (MagicMock(cell_id='sending_cell_1'), 'size1'),  # Sending cell
        (MagicMock(cell_id='receiving_cell_1'), 'size1')  # Receiving cell
    ]
    mock_get_user_id.return_value = 2

    # Mock the order request data
    order_data = {
        "parcel": {
            "length": 10,
            "width": 10,
            "height": 10,
            "weight": 5
        },
        "sending_locker_id": 1,
        "receiving_locker_id": 2,
        "recipient_id": {
            "email": "test@example.com",
            "phone": "1234567890",
            "name": "Test User"
        }
    }

    response = client.post("/api/v1/order/", json=order_data , headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "order_id": 1,
        "message": 'Successfully created',
        "parcel_size": 'size1',
        "sender_id": 1
    }

# # Test error when no available cell in sending locker
# @patch('order.get_db')
# @patch('order.get_current_user')
# @patch('order.find_available_cell')
# @patch('order.change_cell_occupied')
# @patch('order.get_user_id_by_recipient_info')
# def test_create_order_no_sending_cell(mock_get_user, mock_find_cell, mock_change_cell, mock_get_user_id, mock_get_db, mock_current_user, mock_db_session):
#     # Mock database session
#     mock_get_db.return_value = mock_db_session
#     mock_get_user.return_value = mock_current_user

#     # Mock function returns
#     mock_find_cell.side_effect = [  # No available cell in sending locker
#         (None, None),
#         (MagicMock(cell_id='receiving_cell_1'), 'size1')
#     ]
#     mock_get_user_id.return_value = 2

#     # Mock the order request data
#     order_data = {
#         "parcel": {
#             "length": 10,
#             "width": 10,
#             "height": 10,
#             "weight": 5
#         },
#         "sending_locker_id": 1,
#         "receiving_locker_id": 2,
#         "recipient_id": {
#             "email": "test@example.com",
#             "phone": "1234567890",
#             "name": "Test User"
#         }
#     }

#     response = client.post("/", json=order_data)

#     assert response.status_code == 400
#     assert response.json() == {"detail": "No available cells in the sending locker"}

# # Test error when no available cell in receiving locker
# @patch('order.get_db')
# @patch('order.get_current_user')
# @patch('order.find_available_cell')
# @patch('order.change_cell_occupied')
# @patch('order.get_user_id_by_recipient_info')
# def test_create_order_no_receiving_cell(mock_get_user, mock_find_cell, mock_change_cell, mock_get_user_id, mock_get_db, mock_current_user, mock_db_session):
#     # Mock database session
#     mock_get_db.return_value = mock_db_session
#     mock_get_user.return_value = mock_current_user

#     # Mock function returns
#     mock_find_cell.side_effect = [
#         (MagicMock(cell_id='sending_cell_1'), 'size1'),  # Sending cell
#         (None, None)  # No available cell in receiving locker
#     ]
#     mock_get_user_id.return_value = 2

#     # Mock the order request data
#     order_data = {
#         "parcel": {
#             "length": 10,
#             "width": 10,
#             "height": 10,
#             "weight": 5
#         },
#         "sending_locker_id": 1,
#         "receiving_locker_id": 2,
#         "recipient_id": {
#             "email": "test@example.com",
#             "phone": "1234567890",
#             "name": "Test User"
#         }
#     }

#     response = client.post("/", json=order_data)

#     assert response.status_code == 400
#     assert response.json() == {"detail": "No available cells in the receiving locker"}

# # Test exception handling
# @patch('order.get_db')
# @patch('order.get_current_user')
# @patch('order.find_available_cell')
# @patch('order.change_cell_occupied')
# @patch('order.get_user_id_by_recipient_info')
# def test_create_order_exception(mock_get_user, mock_find_cell, mock_change_cell, mock_get_user_id, mock_get_db, mock_current_user, mock_db_session):
#     # Mock database session
#     mock_get_db.return_value = mock_db_session
#     mock_get_user.return_value = mock_current_user

#     # Mock function to raise exception
#     mock_find_cell.side_effect = Exception("Database error")

#     # Mock the order request data
#     order_data = {
#         "parcel": {
#             "length": 10,
#             "width": 10,
#             "height": 10,
#             "weight": 5
#         },
#         "sending_locker_id": 1,
#         "receiving_locker_id": 2,
#         "recipient_id": {
#             "email": "test@example.com",
#             "phone": "1234567890",
#             "name": "Test User"
#         }
#     }

#     response = client.post("/", json=order_data)

#     assert response.status_code == 500
#     assert response.json() == {"detail": "Database error"}
