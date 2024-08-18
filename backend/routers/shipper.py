from datetime import datetime, timedelta
from sqlalchemy import DateTime
from fastapi import APIRouter, HTTPException, Depends,Query
from pydantic import BaseModel, EmailStr, Field
from database.session import get_db
from models.shipper import Shipper
from models.order import Order
from models.locker import Locker, Cell
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from auth.utils import get_current_user, authenticate_user, bcrypt_context
from starlette import status
from enum import Enum
from uuid import UUID
from decouple import config

router = APIRouter(
    prefix="/shipper",
    tags=["shipper"],
    dependencies=[Depends(get_current_user)]
)

public_router = APIRouter(
    prefix="/shipper",
    tags=["shipper"]
)

class ShipperOrderResponse(BaseModel):
    order_id: int
    sending_locker_address: str
    sending_locker_latitude: int
    sending_locker_longitude: int
    receiving_locker_address: str
    receiving_locker_latitude: int
    receiving_locker_longitude: int
    route: Optional[str] = None
    time: Optional[str] = None

# Get information of the order and address of locker by order_id 
@router.get('/{order_id}/shipper_order_info', response_model=ShipperOrderResponse)
async def get_shipper_order_info(order_id: int, db: Session = Depends(get_db)):
    # Query the order details by order_id
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Get the sending and receiving cells
    sending_cell = db.query(Cell).filter(Cell.cell_id == order.sending_cell_id).first()
    receiving_cell = db.query(Cell).filter(Cell.cell_id == order.receiving_cell_id).first()
    if not sending_cell or not receiving_cell:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cells not found")
    
    # Get the lockers associated with the sending and receiving cells
    sending_locker = db.query(Locker).filter(Locker.locker_id == sending_cell.locker_id).first()
    receiving_locker = db.query(Locker).filter(Locker.locker_id == receiving_cell.locker_id).first()
    if not sending_locker or not receiving_locker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lockers not found")
    
    order_info = {
        "order_id": order.order_id,
        "sender_id": order.sender_id,
        "recipient_id": order.recipient_id,
        "sending_locker_address": sending_locker.address,
        "sending_locker_latitude": sending_locker.latitude,
        "sending_locker_longitude": sending_locker.longitude,
        "receiving_locker_address": receiving_locker.address,
        "receiving_locker_latitude": receiving_locker.latitude,
        "receiving_locker_longitude": receiving_locker.longitude,
        "route": Optional[str],
        "time": Optional[str]
    }
    
    return order_info
