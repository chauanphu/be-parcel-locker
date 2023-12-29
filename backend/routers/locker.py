from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database.session import get_db
from models.locker import Locker
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/locker",
    tags=["locker"],
)

class LockerStatusRequest(BaseModel):
    cell_id: int
    occupied: bool

class LockerStatusResponse(BaseModel):
    locker_id: int
    cell_id: int
    occupied: bool

class LockerResponse(BaseModel):
    locker_id: int
    address: str
    latitude: float
    longitude: float
    cells: Optional[list[LockerStatusResponse]] = None

@router.get("/", response_model=list[LockerResponse])
async def get_lockers(db: Session = Depends(get_db)):
    return db.query(Locker).all()

@router.get("/{locker_id}", response_model=LockerResponse)
async def get_locker(locker_id: int, db: Session = Depends(get_db)):
    return db.query(Locker).filter(Locker.locker_id == locker_id).first()

@router.put("/{locker_id}", response_model=LockerResponse)
async def update_locker(locker_id: int, locker: LockerStatusRequest, db: Session = Depends(get_db)):
    db_locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    db_locker.cells[locker.cell_id].occupied = locker.occupied
    db.commit()
    db.refresh(db_locker)
    return db_locker