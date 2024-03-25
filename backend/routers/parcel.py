from datetime import date
from fastapi import APIRouter, Depends, status
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.utils import get_current_user
from sqlalchemy.orm import Session
from database.session import get_db
from models.parcel import Parcel
from models.parcel_type import ParcelType

router = APIRouter(
    prefix="/parcel",
    tags=["parcel"],
    dependencies=[Depends(get_current_user)]
)
class ParcelRequest(BaseModel):
    order_id: float
    width: float
    length: float
    height: float
    weight: float
    parcel_size: str

class ParcelTypeRequest(BaseModel):
    name: str

#create a parcel
@router.post("/", response_model=ParcelRequest)
def create_parcel(parcel: ParcelRequest, db: Session = Depends(get_db)):
    new_parcel = Parcel(**parcel.model_dump())
    db.add(new_parcel)
    db.commit()
    db.refresh(new_parcel)
    return new_parcel

# @router.post("/", response_model=ParcelRequest)
# def create_parcel(parcel: ParcelRequest, db: Session = Depends(get_db)):
#     new_parcel = Parcel(**parcel.model_dump())
#     db.add(new_parcel)
#     db.commit()
#     db.refresh(new_parcel)
#     return new_parcel

# @router.post("/", response_model=ParcelRequest)
# def create_parcel(parcel: ParcelRequest, db: Session = Depends(get_db)):
#     new_parcel = Parcel(**parcel.model_dump())
#     db.add(new_parcel)
#     db.commit()
#     db.refresh(new_parcel)
#     return new_parcel

#get a parcel by parcel_id
@router.get("/{parcel_id}", response_model=ParcelRequest)
def get_parcel(parcel_id: str, db: Session = Depends(get_db)):
    parcel = db.query(Parcel).filter(Parcel.parcel_id == parcel_id).first()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel

#update a parcel by parcel_id
@router.put("/{parcel_id}", response_model=ParcelRequest)
def update_parcel(parcel_id: str, parcel: ParcelRequest, db: Session = Depends(get_db)):
    parcel_put = db.query(Parcel).filter(Parcel.parcel_id == parcel_id).update(
        parcel.model_dump(), synchronize_session=False
    )
    db.commit()
    return parcel

# delete a parcel
@router.delete("/{parcel_id}", response_model=ParcelRequest)
def delete_parcel(parcel_id: str, db: Session = Depends(get_db)):
    parcel = db.query(Parcel).filter(Parcel.parcel_id == parcel_id).first()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    db.delete(parcel)
    db.commit()
    return parcel

#create a parcel type
@router.post("/type", response_model=ParcelTypeRequest)
def create_parcel_type(parcel_type: ParcelTypeRequest, db: Session = Depends(get_db)):
    new_parcel_type = ParcelType(**parcel_type.model_dump())
    db.add(new_parcel_type)
    db.commit()
    db.refresh(new_parcel_type)
    return new_parcel_type


