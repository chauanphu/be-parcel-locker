# test_main.py
import sys
import os
import subprocess
from datetime import datetime
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

@pytest.fixture(scope="session", autouse=True)
def backup_and_restore_db():
    # Define backup and restore operations
    db_container_name = 'backend-db-1'
    db_user = 'admin'
    db_name = 'parcel'
    backup_file = f"backup_{db_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
    
    def backup_database():
        command = f"docker exec {db_container_name} pg_dump -U {db_user} {db_name} > {backup_file}"
        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Backup successful! File saved as {backup_file}")
        except subprocess.CalledProcessError as e:
            print(f"Backup failed: {e}")
    
    def restore_database():
        command = f"docker exec {db_container_name} psql -U {db_user} -d {db_name} -f {backup_file}"
        try:
            subprocess.run(command, shell=True, check=True)
            print("Database restored to original state")
        except subprocess.CalledProcessError as e:
            print(f"Restore failed: {e}")
    
    # Backup the database before running tests
    backup_database()

    try:
        yield  # Run the tests
    finally:
        # Restore the database after tests
        restore_database()

        # Optionally, remove the backup file
        if os.path.exists(backup_file):
            os.remove(backup_file)


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db_session():
    return mock_session


# Additional tests can be added here
