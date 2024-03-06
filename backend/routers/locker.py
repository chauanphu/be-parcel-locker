from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database.session import get_db
from models.locker import Locker, LockerStatus
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from auth.utils import get_current_user
router = APIRouter(
    prefix="/locker",
    tags=["locker"],
    dependencies=[Depends(get_current_user)]
)

class LockerStatusRequest(BaseModel):
    cell_id: int
    occupied: bool

class LockerStatusResponse(BaseModel):
    cell_id: int
    occupied: bool

class LockerResponse(BaseModel):
    locker_id: int
    address: str
    latitude: float
    longitude: float
    cells: List[LockerStatusResponse]

@router.get("/", response_model=List[LockerResponse])
async def get_lockers(db: Session = Depends(get_db)):
    return db.query(Locker).all()

@router.get("/{locker_id}", response_model=LockerResponse)
async def get_locker(locker_id: int, db: Session = Depends(get_db)):
    locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    if not locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    return locker

@router.put("/{locker_id}", response_model=int)
async def update_locker(locker_id: int, _locker: LockerStatusRequest, db: Session = Depends(get_db)):
    db_locker = db.query(LockerStatus).filter(LockerStatus.locker_id == locker_id).update(_locker.model_dump(
        exclude_unset=True, 
        exclude_none=True
        ))
    if not db_locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    db.commit()
    # Return 200 OK
    return locker_id