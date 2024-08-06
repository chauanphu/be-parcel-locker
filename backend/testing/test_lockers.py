# import pytest
# from fastapi.testclient import TestClient
# from datetime import datetime
# from uuid import uuid4
# from main import app
# from routers import api_router
# from models.locker import Locker, Cell
# from sqlalchemy.orm import Session

# client=TestClient(api_router)

# # def test_create_locker(test_app: TestClient, db_session: Session):
# #     response = test_app.post("/locker/", json={
# #         "address": "Test Address",
# #         "latitude": 10.0,
# #         "longitude": 10.0
# #     })
# #     assert response.status_code == 200
# #     locker_id = response.json()
# #     locker = db_session.query(Locker).filter(Locker.locker_id == locker_id).first()
# #     assert locker is not None
# #     assert locker.address == "Test Address"

# # def test_get_lockers_by_paging(test_app: TestClient, db_session: Session):
# #     response = test_app.get("/locker2/?page=1&per_page=10")
# #     assert response.status_code == 200
# #     data = response.json()
# #     assert "total" in data
# #     assert "page" in data
# #     assert "per_page" in data
# #     assert "total_pages" in data
# #     assert "data" in data

# # def test_get_locker(test_app: TestClient, db_session: Session):
# #     locker = Locker(address="Test Address", latitude=10.0, longitude=10.0, locker_status="Active", date_created=datetime.utcnow())
# #     db_session.add(locker)
# #     db_session.commit()
# #     db_session.refresh(locker)
    
# #     response = test_app.get(f"/locker/{locker.locker_id}")
# #     assert response.status_code == 200
# #     data = response.json()
# #     assert data["locker_id"] == locker.locker_id
# #     assert data["address"] == locker.address

# # def test_create_cell(test_app: TestClient, db_session: Session):
# #     locker = Locker(address="Test Address", latitude=10.0, longitude=10.0, locker_status="Active", date_created=datetime.utcnow())
# #     db_session.add(locker)
# #     db_session.commit()
# #     db_session.refresh(locker)

# #     response = test_app.post(f"/locker/{locker.locker_id}/cell", json={
# #         "size": "M"
# #     })
# #     assert response.status_code == 200
# #     cell_id = response.json()
# #     cell = db_session.query(Cell).filter(Cell.cell_id == cell_id).first()
# #     assert cell is not None
# #     assert cell.size == "M"

# # def test_get_density(test_app: TestClient, db_session: Session):
# #     locker = Locker(address="Test Address", latitude=10.0, longitude=10.0, locker_status="Active", date_created=datetime.utcnow())
# #     db_session.add(locker)
# #     db_session.commit()
# #     db_session.refresh(locker)

# #     for _ in range(10):
# #         cell = Cell(locker_id=locker.locker_id, size="M", occupied=False, date_created=datetime.utcnow())
# #         db_session.add(cell)
# #     db_session.commit()

# #     response = test_app.get(f"/locker/{locker.locker_id}/density")
# #     assert response.status_code == 200
# #     data = response.json()
# #     assert data["total_cells"] == 10
# #     assert data["occupied_cells"] == 0
# #     assert data["density"] == 0
# #     assert data["density_status"] == "Free"

# def test_test1(test_app: TestClient, db_session: Session):
#     response = test_app.get("/locker2/test")
#     assert response.status_code == 200
#     assert response.json() == "Server is running, test successful"


# # def test_test2():
# #     respone = client.get("/locker2/test")
# #     assert respone.status_code == 200
# #     assert respone.json() == "Server is running, test successful"