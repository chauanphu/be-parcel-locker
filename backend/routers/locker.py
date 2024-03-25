from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database.session import get_db
from models.locker import Locker, Cell
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from auth.utils import get_current_user
from uuid import UUID

from models.order import Order

router = APIRouter(
    prefix="/locker",
    tags=["locker"],
    dependencies=[Depends(get_current_user)]
)

class CellRequest(BaseModel):
    cell_id: UUID
    occupied: bool

class CellResponse(BaseModel):
    cell_id: UUID
    occupied: bool
    
class CellIDResponse(BaseModel):
    cell_id : UUID
    is_sending : bool
    
class CellIDRequest(BaseModel):
    locker_id : int
    order_id : UUID

class LockerResponse(BaseModel):
    locker_id: int
    address: str
    latitude: float
    longitude: float
    cells: List[CellResponse]

class LockerInfoResponse(BaseModel):
    address: str
    latitude: float
    longitude: float

class LockerCreateRequest(BaseModel):
    address: str
    latitude: float
    longitude: float

@router.get("/", response_model=List[LockerResponse])
async def get_lockers(db: Session = Depends(get_db)):
    return db.query(Locker).all()

@router.get("/{locker_id}", response_model=LockerResponse)
async def get_locker(locker_id: int, db: Session = Depends(get_db)):
    # Get locker by id
    locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    # If not found, raise 404
    if not locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    return locker

# Get cell by locker_id and order_id
@router.get("/{locker_id}/{order_id}", response_model=CellIDResponse)
async def get_cell(locker_id: int, order_id: int, db: Session = Depends(get_db)):
    # Get cell by locker_id and order_id
    query = db.query(Order).filter(Order.order_id == order_id)
    # is_sending = False
    # if not query.first():
    #     raise HTTPException(status_code=404, detail="Order not found")
    # if not query.first().sending_date is None:
    #     cell = 
    # # If not found, raise 404
    # if not cell:
    #     raise HTTPException(status_code=404, detail="Cell not found")
    return 1

@router.post("/", response_model=int)
async def create_locker(locker: LockerCreateRequest, db: Session = Depends(get_db)):
    # Add new locker
    locker = Locker(**locker.model_dump())
    db.add(locker)
    db.commit()
    db.refresh(locker)
    return locker.locker_id

@router.post("/{locker_id}/cell", response_model=UUID)
async def create_cell(locker_id: int, db: Session = Depends(get_db)):
    # Add new cell
    cell = Cell(locker_id=locker_id)
    db.add(cell)
    db.commit()
    db.refresh(cell)
    return cell.cell_id

@router.put("/{locker_id}", response_model=int)
async def update_locker(locker_id: int, _locker: CellRequest, db: Session = Depends(get_db)):
    # Update locker status, allow partial update
    db_locker = db.query(Cell).filter(Cell.locker_id == locker_id).update(_locker.model_dump(
        exclude_unset=True, 
        exclude_none=True
        ))
    # If not found, raise 404
    if not db_locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    db.commit()
    # Return 200 OK
    return locker_id