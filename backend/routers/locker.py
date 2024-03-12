from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database.session import get_db
from models.locker import Locker, Cell
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from auth.utils import get_current_user

router = APIRouter(
    prefix="/locker",
    tags=["locker"],
    dependencies=[Depends(get_current_user)]
)

class CellRequest(BaseModel):
    cell_id: int
    occupied: bool

class CellResponse(BaseModel):
    cell_id: int
    occupied: bool

class LockerResponse(BaseModel):
    locker_id: int
    address: str
    latitude: float
    longitude: float
    cells: List[CellResponse]

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