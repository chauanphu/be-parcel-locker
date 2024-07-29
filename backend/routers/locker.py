from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from database.session import get_db
from models.locker import Locker, Cell
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from pydantic import BaseModel
from auth.utils import get_current_user
from uuid import UUID
from enum import Enum

from models.order import Order

class SizeEnum(str, Enum):
    S = 'S'
    M = 'M'
    L = 'L'
    
class StatusEnum(str, Enum):
    Active = 'Active'
    Inactive = 'Inactive'   

router = APIRouter(
    prefix="/locker",
    tags=["locker"],
    dependencies=[Depends(get_current_user)]
)

class CellRequestCreate(BaseModel):
    size: SizeEnum

class CellResponse(BaseModel):
    cell_id: UUID   
    occupied: bool
    size: SizeEnum
    
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
    status: str
    cells: List[CellResponse]

class LockerInfoResponse(BaseModel):
    address: str
    latitude: float
    longitude: float

class LockerCreateRequest(BaseModel):
    address: str
    latitude: float
    longitude: float
    status: StatusEnum

@router.get("/", response_model=List[LockerResponse])
async def get_lockers(db: Session = Depends(get_db)):
    return db.query(Locker).all()

# @router.get("/", response_model=Dict[str, Any])
# async def get_lockers(
#     db: Session = Depends(get_db),
#     limit: int = Query(default=3, ge=1),  # Default limit is 10, minimum value is 1
#     offset: int = Query(default=0, ge=0)   # Default offset is 0, minimum value is 0
# ):
#     total = db.query(func.count(Locker.id)).scalar()
#     lockers = db.query(Locker).offset(offset).limit(limit).all()
#     return {
#         "total": total,
#         "limit": limit,
#         "offset": offset,
#         "data": lockers
#     }

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
async def create_locker(locker: LockerInfoResponse, db: Session = Depends(get_db)):
    # Add new locker
    locker = Locker(**locker.model_dump())
    db.add(locker)
    db.commit()
    db.refresh(locker)
    return locker.locker_id

@router.post("/{locker_id}/cell", response_model=UUID)
async def create_cell(locker_id: int, cell_info: CellRequestCreate, db: Session = Depends(get_db)):
    locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    
    # Check if locker is inactive
    if locker is None or locker.status == "inactive":
        raise HTTPException(status_code=400, detail="This locker is inactive")
    # Add new cell
    cell = Cell(locker_id=locker_id, size=cell_info.size)
    db.add(cell)
    db.commit()
    db.refresh(cell)
    return cell.cell_id

@router.put("/{locker_id}", response_model=int)
async def update_locker(locker_id: int, _locker: CellRequestCreate, db: Session = Depends(get_db)):
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

# delete a locker
@router.delete("/{locker_id}")
def delete_locker(locker_id: int, db: Session = Depends(get_db)):
    locker_delete = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    
    if locker_delete == None:
        raise HTTPException(status_code=404, detail="Locker not found")
    
    # Fetch all cells associated with this locker
    cells_delete = db.query(Cell).filter(Cell.locker_id == locker_id).all()
    
    for cell in cells_delete:
        # Delete all orders associated with each cell
        db.query(Order).filter((Order.sending_cell_id == cell.cell_id) | (Order.receiving_cell_id == cell.cell_id)).delete()
    
    # Delete all cells associated with this locker
    db.query(Cell).filter(Cell.locker_id == locker_id).delete()
    
    
    db.delete(locker_delete)
    db.commit()
    return {
        "Message": "Locker deleted sucessfully"
    }

@router.put("/{locker_id}/cell")
async def update_cell_to_false(locker_id: int, db: Session = Depends(get_db)):
    # Update locker status, allow partial update
    db_locker = db.query(Cell).filter(Cell.locker_id == locker_id).all()
    # If not found, raise 404
    if not db_locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    db.query(Cell).filter(Cell.locker_id == locker_id).update({Cell.occupied: False})
    db.commit()
    # Return 200 OK
    return {
        "Message": "All cell occupied successfully updated to false"
    }
