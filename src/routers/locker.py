from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from database.session import get_db
from models.locker import Locker, Cell
from models.order import Order, OrderStatus
from models.parcel import Parcel
from auth.utils import check_admin

class SizeEnum(str, Enum):
    S = 'S'
    M = 'M'
    L = 'L'

class DensityEnum(str, Enum):
    Full = 100
    Busy = 70

class LockerStatusEnum(str, Enum):
    Active = 'Active'
    Inactive = 'Inactive'

class LockerBase(BaseModel):
    """Base Locker model with common fields"""
    address: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class LockerCreate(LockerBase):
    """Model for creating a locker"""
    locker_status: LockerStatusEnum = Field(default=LockerStatusEnum.Active)

class LockerUpdate(BaseModel):
    """Model for updating a locker"""
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    locker_status: Optional[LockerStatusEnum] = None

class CellBase(BaseModel):
    """Base Cell model"""
    size: SizeEnum

class CellCreate(CellBase):
    """Model for creating cells"""
    quantity: int = Field(..., gt=0, le=100)

class CellIDResponse(BaseModel):
    """Model for cell ID response"""
    cell_id: UUID
    size: SizeEnum

class CellResponse(CellBase):
    """Model for cell response"""
    cell_id: UUID
    date_created: datetime

    class Config:
        orm_mode = True

class LockerResponse(LockerBase):
    """Model for locker response"""
    locker_id: int
    locker_status: LockerStatusEnum
    cells: List[CellResponse]
    date_created: datetime

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/api/v1/lockers",
    tags=["lockers"],
)

@router.get(
    "",
    response_model=Dict[str, Any],
    dependencies=[Depends(check_admin)],
    summary="Get all lockers with pagination"
)
async def list_lockers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
):
    total_lockers = db.query(Locker).count()
    lockers = db.query(Locker).offset((page - 1) * per_page).limit(per_page).all()

    locker_responses = []
    for locker in lockers:
        cells = db.query(Cell).filter(Cell.locker_id == locker.locker_id).all()
        locker_responses.append({
            "locker_id": locker.locker_id,
            "address": locker.address,
            "latitude": locker.latitude,
            "longitude": locker.longitude,
            "locker_status": locker.locker_status,
            "date_created": locker.date_created,
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "size": cell.size
                } for cell in cells
            ]
        })

    total_pages = (total_lockers + per_page - 1) // per_page
    return {
        "total_lockers": total_lockers,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": locker_responses
    }

@router.get("/cells", response_model=Dict[str, Any], dependencies=[Depends(check_admin)])
def get_cells_by_paging(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):
    total_cells = db.query(Cell).count()
    cells = db.query(Cell).offset((page - 1) * per_page).limit(per_page).all()
    cell_responses = [
        {
            "locker_id": cell.locker_id,
            "cell_id": cell.cell_id,
            "size": cell.size,
            "date_created": cell.date_created,
        }
        for cell in cells
    ]
    total_pages = (total_cells + per_page - 1) // per_page
    return {
        "total_cells": total_cells,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": cell_responses
    }

@router.get(
    "/{locker_id}/cells",
    response_model=List[CellResponse],
    summary="Get cells for specific locker"
)
async def get_locker_cells(
    locker_id: int,
    db: Session = Depends(get_db)
):
    locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    if not locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    
    cells = db.query(Cell).filter(Cell.locker_id == locker_id).all()
    cell_responses = [
        {
            "cell_id": cell.cell_id,
            "size": cell.size,
            "date_created": cell.date_created
        }
        for cell in cells
    ]
    
    return cell_responses

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_admin)],
    response_model=Dict[str, int],
    summary="Create new locker"
)
async def create_locker(
    locker: LockerCreate,
    db: Session = Depends(get_db)
):
    find_locker = db.query(Locker).filter((Locker.latitude == locker.latitude) & (Locker.longitude == locker.longitude)).first()

    if find_locker is None:
        locker = Locker(**locker.dict())
        db.add(locker)
        db.commit()
        db.refresh(locker)
        return locker.locker_id
    else:
        return {"message": "Locker already exists!"}

@router.get("/{locker_id}/available-cells", response_model=List[CellIDResponse])
async def get_available_cells(locker_id: int, db: Session = Depends(get_db)):
    locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    if not locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    
    used_cells = set()
    incompleted_orders = db.query(Order).filter(Order.order_status == OrderStatus.Completed)
    used_cells.update([order.sending_cell_id for order in incompleted_orders])
    used_cells.update([order.receiving_cell_id for order in incompleted_orders])
    available_cells = db.query(Cell).filter(Cell.cell_id.notin_(used_cells)).all()
    return [
        CellIDResponse(cell_id=cell.cell_id, size=cell.size) for cell in available_cells
    ]

@router.post("/{locker_id}/cells", status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_admin)])
async def create_cells(locker_id: int, cell_info: CellCreate, db: Session = Depends(get_db)):
    locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    
    if locker is None or locker.locker_status == LockerStatusEnum.Inactive:
        raise HTTPException(status_code=400, detail="This locker is inactive")
    
    cells = []
    for _ in range(cell_info.quantity):
        cell = Cell(locker_id=locker_id, size=cell_info.size)
        db.add(cell)
        cells.append(cell)
    
    db.commit()
    for cell in cells:
        db.refresh(cell)
    
    return {"detail": "Cells created successfully"}

@router.put("/{locker_id}", dependencies=[Depends(check_admin)])
async def update_locker(locker_id: int, locker_update: LockerUpdate, db: Session = Depends(get_db)):
    db_locker = db.query(Locker).filter(Locker.locker_id == locker_id).update(locker_update.dict(exclude_unset=True, exclude_none=True))
    if not db_locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    db.commit()
    return {"message": f"Locker_id {locker_id} successfully updated"}

@router.delete("/{locker_id}", dependencies=[Depends(check_admin)])
def delete_locker(locker_id: int, db: Session = Depends(get_db)):
    locker_delete = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    
    if locker_delete is None:
        raise HTTPException(status_code=404, detail="Locker not found")
    
    cells_delete = db.query(Cell).filter(Cell.locker_id == locker_id).all()
    
    for cell in cells_delete:
        orders_delete = db.query(Order).filter((Order.sending_cell_id == cell.cell_id) | (Order.receiving_cell_id == cell.cell_id)).all()
        for order in orders_delete:
            parcel = db.query(Parcel).filter(Parcel.parcel_id == order.order_id).first()
            db.delete(parcel)
            db.delete(order)
            db.commit()
        db.delete(cell)
    
    db.delete(locker_delete)
    db.commit()
    return {"message": "Locker deleted successfully"}