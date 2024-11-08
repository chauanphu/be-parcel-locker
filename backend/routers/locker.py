from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from database.session import get_db
from models.locker import Locker, Cell
from models.order import Order
from models.parcel import Parcel
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from auth.utils import get_current_user,check_admin
from uuid import UUID
from enum import Enum

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
    date_created: datetime
    
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
    locker_status: LockerStatusEnum
    cells: List[CellResponse]
    date_created: datetime
    
class LockerInfoResponse(BaseModel):
    address: str
    latitude: float
    longitude: float

class LockerCreateRequest(BaseModel):
    address: str
    latitude: float
    longitude: float
    locker_status: LockerStatusEnum
    
class LockerUpdateRequest(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    locker_status: Optional[LockerStatusEnum] = None

class DensityResponse(BaseModel):
    locker_id: int
    total_cells: int
    occupied_cells: int
    density: float
    density_status: str

# @router.get("/{locker_id}", response_model=LockerResponse)
# async def get_locker(locker_id: int, db: Session = Depends(get_db)):
#     # Get locker by id
#     locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
#     # If not found, raise 404
#     if not locker:
#         raise HTTPException(status_code=404, detail="Locker not found")
#     return locker

#get locker by paging
@router.get("/lockers", response_model=Dict[str, Any],dependencies=[Depends(check_admin)])
async def get_lockers_by_paging(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),  # Current page number for lockers
    per_page: int = Query(10, ge=1),  # Number of lockers per page
):
        # Pagination for lockers
        total_lockers = db.query(Locker).count()
        lockers = db.query(Locker).offset((page - 1) * per_page).limit(per_page).all()

        locker_responses = []
        for locker in lockers:
            # Pagination for cells within each locker
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
                        "occupied": cell.occupied,
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

#get cell by paging
@router.get("/cells", response_model=Dict[str, Any],dependencies=[Depends(check_admin)])
def get_cells_by_paging(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):
        # Total number of cells
        total_cells = db.query(Cell).count()
        
        # Fetch paginated list of cells
        cells = db.query(Cell).offset((page - 1) * per_page).limit(per_page).all()
        # Format the response
        cell_responses = [
            {
                "locker_id": cell.locker_id,
                "cell_id": cell.cell_id,
                "occupied": cell.occupied,
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
    

@router.post("/", dependencies=[Depends(check_admin)])
async def create_locker(locker: LockerInfoResponse, db: Session = Depends(get_db)):
    find_locker = db.query(Locker).filter((Locker.latitude == locker.latitude)&(Locker.longitude == locker.longitude)).first()

    if find_locker == None:
        # Add new locker
        locker = Locker(**locker.model_dump())
        db.add(locker)
        db.commit()
        db.refresh(locker)
        return locker.locker_id
    else:
        return {"Message: Locker existed!"}

@router.post("/{locker_id}/cell", response_model=UUID,dependencies=[Depends(check_admin)])
async def create_cell(locker_id: int, cell_info: CellRequestCreate, db: Session = Depends(get_db)):
    locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    
    # Check if locker is inactive
    if locker is None or locker.locker_status == "Inactive":
        raise HTTPException(status_code=400, detail="This locker is inactive")
    # Add new cell
    cell = Cell(locker_id=locker_id, size=cell_info.size)
    db.add(cell)
    db.commit()
    db.refresh(cell)
    return cell.cell_id

# Update locker by locker_id
@router.put("/{locker_id}",dependencies=[Depends(check_admin)])
async def update_locker(locker_id: int, _locker: LockerUpdateRequest, db: Session = Depends(get_db)):
    # Update locker status, allow partial update
    db_locker = db.query(Locker).filter(Locker.locker_id == locker_id).update(_locker.model_dump(
        exclude_unset=True, 
        exclude_none=True
        ))
    # If not found, raise 404
    if not db_locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    db.commit()
    # Return 200 OK
    return {
         "Message": f"Locker_id {locker_id} successfully updated"
    }

# delete a locker
@router.delete("/{locker_id}",dependencies=[Depends(check_admin)])
def delete_locker(locker_id: int, db: Session = Depends(get_db)):
    locker_delete = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    
    if locker_delete == None:
        raise HTTPException(status_code=404, detail="Locker not found")
    
    # Fetch all cells associated with this locker
    cells_delete = db.query(Cell).filter(Cell.locker_id == locker_id).all()
    
    for cell in cells_delete:
        # Delete all orders associated with each cell
        orders_delete = db.query(Order).filter((Order.sending_cell_id == cell.cell_id) | (Order.receiving_cell_id == cell.cell_id)).all()
        for order in orders_delete:
            # if order == None:
            #     raise HTTPException(status_code=404, detail="Order not found")
            parcel =  db.query(Parcel).filter(Parcel.parcel_id == order.order_id).first()
            # if parcel == None:
            #     raise HTTPException(status_code=404, detail="Parcel not found")
            db.delete(parcel)
            db.delete(order)
            db.commit()
        db.delete(cell)
    # # Delete all cells associated with this locker
    # db.query(Cell).filter(Cell.locker_id == locker_id).delete()
    
    
    db.delete(locker_delete)
    db.commit()
    return {
        "Message": "Locker deleted sucessfully"
    }

# Get density of occupied cells by locker_id
@router.get("/{locker_id}/size/{size}/density", response_model=DensityResponse)
def get_density(locker_id: int, size: SizeEnum, db: Session = Depends(get_db)):
    
    # Get all cells in size in the locker
    all_cells_count = db.query(Cell).filter(Cell.locker_id == locker_id, Cell.size == size).count()
    
    # Get occupied cells of a specific size in the locker
    occupied_cells_count = db.query(Cell).filter(Cell.locker_id == locker_id, Cell.size == size, Cell.occupied == True).count()
    
    # If no cells are found, raise 404
    if all_cells_count == 0:
        raise HTTPException(status_code=404, detail="Locker not found or no cells in the locker")
    
    # Calculate the density of occupied cells
    density = round((occupied_cells_count / all_cells_count), 2) * 100
    
    if density == int(DensityEnum.Full.value):
        density_status = "Full"
    elif density >= int(DensityEnum.Busy.value):
        density_status = "Busy"
    else:
        density_status = "Free"
        
    return DensityResponse(
        locker_id = locker_id,
        total_cells = all_cells_count,
        occupied_cells = occupied_cells_count,
        density = density,
        density_status = density_status
    )
    