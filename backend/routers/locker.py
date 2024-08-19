from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from database.session import get_db
from models.locker import Locker, Cell
from models.order import Order
from models.parcel import Parcel
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from pydantic import BaseModel
from auth.utils import get_current_user
from uuid import UUID
from enum import Enum

class SizeEnum(str, Enum):
    S = 'S'
    M = 'M'
    L = 'L'
    
class LockerStatusEnum(str, Enum):
    Active = 'Active'
    Inactive = 'Inactive'   

router = APIRouter(
    prefix="/locker",
    tags=["locker"],
    dependencies=[Depends(get_current_user)]
)
router2 = APIRouter(
    prefix="/locker2",
    tags=["locker2"],
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

class DensityResponse(BaseModel):
    locker_id: int
    total_cells: int
    occupied_cells: int
    density: float
    density_status: str

# @router.get("/", response_model=List[LockerResponse])
# async def get_lockers(db: Session = Depends(get_db)):
#     return db.query(Locker).all()

@router2.get("/", response_model=Dict[str, Any])
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
            "total": total_lockers,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": locker_responses
        }

@router.get("/{locker_id}", response_model=LockerResponse)
async def get_locker(locker_id: int, db: Session = Depends(get_db)):
    # Get locker by id
    locker = db.query(Locker).filter(Locker.locker_id == locker_id).first()
    # If not found, raise 404
    if not locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    return locker


#get cell by paging
@router.get("/", response_model=Dict[str, Any])
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
            "total": total_cells,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": cell_responses
        }
    

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
    if locker is None or locker.locker_status == "Inactive":
        raise HTTPException(status_code=400, detail="This locker is inactive")
    # Add new cell
    cell = Cell(locker_id=locker_id, size=cell_info.size)
    db.add(cell)
    db.commit()
    db.refresh(cell)
    return cell.cell_id

# Update locker by locker_id
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
    
@router.put("/{order_id}/update sending cell occupied to False")
async def update_cell_to_false(order_id: int, db: Session = Depends(get_db)):
    # Get the order by order_id
    db_order = db.query(Order).filter(Order.order_id == order_id).first()
    # If not found, raise 404
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get the sending cell and update its occupied status to False
    sending_cell_id = db_order.sending_cell_id
    db_cell = db.query(Cell).filter(Cell.cell_id == sending_cell_id).first()
    
    # If the sending cell is not found, raise 404
    if not db_cell:
        raise HTTPException(status_code=404, detail="Sending cell not found")
    if db_cell.occupied == False:
        return {
             "Message": "the sending cell is already occupied false"
        }
    db_cell.occupied = False
    db.commit()
    
    # Return 200 OK
    return {
        "Message": f"Sending cell occupied of order_id: {order_id} successfully updated to false"
    }
    
@router.put("/{order_id}/update receiving cell occupied to False")
async def update_cell_to_false(order_id: int, db: Session = Depends(get_db)):
    # Get the order by order_id
    db_order = db.query(Order).filter(Order.order_id == order_id).first()
    # If not found, raise 404
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get the receiving cell and update its occupied status to False
    receiving_cell_id = db_order.receiving_cell_id
    db_cell = db.query(Cell).filter(Cell.cell_id == receiving_cell_id).first()
    
    # If the receiving cell is not found, raise 404
    if not db_cell:
        raise HTTPException(status_code=404, detail="Receiving cell not found")
    if db_cell.occupied == False:
        return {
             "Message": "the receiving cell is already occupied false"
        }
    db_cell.occupied = False
    db.commit()
    
    # Return 200 OK
    return {
        "Message":  f"Receiving cell occupied of order_id: {order_id} successfully updated to false"
    }

# Get density of occupied cells by locker_id
@router.get("/{locker_id}/density", response_model=DensityResponse)
def get_density(locker_id: int, db: Session = Depends(get_db)):
    
    # Get all cells in the locker
    all_cells_count = db.query(Cell).filter(Cell.locker_id == locker_id).count()
    
    # Get occupied cells in the locker
    occupied_cells_count = db.query(Cell).filter(Cell.locker_id == locker_id, Cell.occupied == True).count()
    
    # If no cells are found, raise 404
    if all_cells_count == 0:
        raise HTTPException(status_code=404, detail="Locker not found or no cells in the locker")
    
    # Calculate the density of occupied cells
    density = round((occupied_cells_count / all_cells_count), 2) * 100
    
    if density == 100:
        density_status = "Full"
    elif density >= 70:
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
    
    
# @router2.get("/test")
# def test_server():
#     return "Server is running, test successful"
    