from datetime import datetime, timedelta
from sqlalchemy import DateTime
from fastapi import APIRouter, HTTPException, Depends,Query
from pydantic import BaseModel, EmailStr, Field
from models.account import Account
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

# public_router = APIRouter(
#     prefix="/shipper",
#     tags=["shipper"]
# )

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

class RegisterShipperRequest(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str
    role: int = 3
    
  
@router.post('/create_shipper', status_code=status.HTTP_201_CREATED)
async def create_shipper(create_shipper_request: RegisterShipperRequest, db: Session = Depends(get_db)):
    # Check if passwords match
    if create_shipper_request.password != create_shipper_request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')
    
    # Check if the username or email already exists
    existing_user = db.query(Account).filter(
        (Account.username == create_shipper_request.username) 
        (Account.email == create_shipper_request.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username or email already exists')
    
    # Hash the password
    hashed_password = bcrypt_context.hash(create_shipper_request.password)
    
    # Create new account with role = 3 (Shipper)
    new_account = Account(
        email=create_shipper_request.email,
        name=create_shipper_request.username,
        password=hashed_password,
        role=3  # Role for Shipper
    )
    
    # Add the new account to the database
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return {"message": "Shipper account created successfully", 
            "shipper_id": new_account.user_id,
            "role": new_account.role}


#GET PAGING SHIPPER
@router.get("/", response_model=Dict[str, Any])
def get_paging_shippers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):
    # Total number of shippers
    total_shippers = db.query(Shipper).count()

    # Fetch paginated list of shippers
    shippers = db.query(Shipper).offset((page - 1) * per_page).limit(per_page).all()

    # Format the response
    shipper_responses = [
        {
            "shipper_id": shipper.shipper_id,
            "order_id": shipper.order_id,
            "name": shipper.name,
            "gender": shipper.gender,
            "age": shipper.age,
            "phone": shipper.phone,
            "address": shipper.address,
        }
        for shipper in shippers
    ]

    total_pages = (total_shippers + per_page - 1) // per_page
    return {
        "total": total_shippers,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": shipper_responses
    }


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
