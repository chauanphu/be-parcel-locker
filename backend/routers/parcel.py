from datetime import date
from fastapi import APIRouter, Depends, status
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.utils import get_current_user
from sqlalchemy.orm import Session
from database.session import get_db
from models.parcel import Parcel

router = APIRouter(
    prefix="/parcel",
    tags=["parcel"],
    dependencies=[Depends(get_current_user)]
)
class ParcelRequest(BaseModel):
    width: float
    length: float
    height: float
    weight: float
    parcel_size: str


@router.post("/", response_model=ParcelRequest)
def create_parcel(parcel: ParcelRequest, db: Session = Depends(get_db)):
    new_parcel = Parcel(**parcel.dict())
    db.add(new_parcel)
    db.commit()
    db.refresh(new_parcel)
    return new_parcel


