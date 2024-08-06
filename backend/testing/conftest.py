# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import StaticPool,create_engine
# from sqlalchemy.orm import sessionmaker
# from decouple import config
# import sys
# import os
# from sqlalchemy.orm import Session
# from unittest.mock import MagicMock

# # # Assuming you want to import from the parent directory
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from main import app  
# from database import Base  
# from database.session import get_db


# mock_session = MagicMock()
# # Override the database dependency with the test database session
# def override_get_db():
#     try:
#         yield mock_session
#     finally:
#         pass

# app.dependency_overrides[get_db] = override_get_db

# @pytest.fixture
# def mock_db_session():
#     return mock_session