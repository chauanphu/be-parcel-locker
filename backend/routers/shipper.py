import random
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, Field
from models.account import Account
from models.role import Role
from models.order import Order, OrderStatus
from database.session import get_db
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from auth.utils import get_current_user, hash_password
from starlette import status

from states import shipment
from utils.redis import redis_client
from utils.mqtt import locker_client

router = APIRouter(
    prefix="/shipper",
    tags=["shipper"],
    dependencies=[Depends(get_current_user)]
)

class OrderInforSchema(BaseModel):
    order_id: int
    sending_locker_address: str
    sending_locker_latitude: int
    sending_locker_longitude: int
    receiving_locker_address: str
    receiving_locker_latitude: int
    receiving_locker_longitude: int
    route: Optional[str] = None
    time: Optional[str] = None

class CreateShipperSchema(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str
    role: int = 3
    
@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_shipper(create_shipper_request: CreateShipperSchema, db: Session = Depends(get_db)):
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
    hashed_password = hash_password(create_shipper_request.password)
    
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
    role_shipper = db.query(Role).filter(Role.name == "shipper").first()
    if not role_shipper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role 'shipper' not found")
    view_shippers = db.query(Account).filter(Account.role == role_shipper.role_id)
    total_shippers = view_shippers.count()
    # Fetch paginated list of shippers
    shippers = view_shippers.limit(per_page).offset((page - 1) * per_page).all()

    # Format the response
    shipper_responses = [
        {
            "shipper_id": shipper.user_id,
            "name": shipper,
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

#### SHIPPER ROUTES ####
@router.post("/accept/{route_id}")
def accept_route(route_id: int, db: Session = Depends(get_db)):
    pass

@router.post("/reject/{route_id}")
def reject_route(route_id: int, db: Session = Depends(get_db)):
    pass
#########################

#### ON PICKUP AND DELIVER ####
# Handling cell unlock by POST request
def verify_shipper_order(order_id: int, otp: int, db: Session, current_user: Account, status: OrderStatus = OrderStatus.Waiting) -> Order:
    """Common verification function for shipper operations"""
    if current_user.role_rel.name != "shipper":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only shippers can perform this action")
    
    order: Order = db.query(Order).filter(
        Order.order_id == order_id, 
        Order.shipper_id == current_user.user_id,
        Order.order_status == status
    ).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Verify OTP if provided
    if otp:
        stored_otp = redis_client.get(f"otp:{order_id}")
        if not stored_otp:
            raise HTTPException(status_code=400, detail="OTP code not found or expired")
        if int(stored_otp) != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    return order

@router.post("/generate_qr")
def unlock_cell(order_id: int, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    order = verify_shipper_order(order_id, None, db, current_user)
    
    # Generate OTP code
    otp = random.randint(100000, 999999)
    redis_client.setex(f"otp:{order_id}", 300, otp)
    locker_client.print_qr(order.sending_locker_id, order_id, code=otp)
    
    return {"message": "QR code generated successfully"}

@router.post("/pickup/{order_id}")
def pickup_order(order_id: int, otp: int, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    if otp is None:
        raise HTTPException(status_code=400, detail="OTP code is required")
    order = verify_shipper_order(order_id, otp, db, current_user)
    
    order.order_status = OrderStatus.Ongoing
    db.commit()
    
    shipment.pickup_order(order_id)
    return {"message": "Order picked up successfully"}

@router.post("/deliver/{order_id}")
def deliver_order(order_id: int, otp: int, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    if otp is None:
        raise HTTPException(status_code=400, detail="OTP code is required")
    order = verify_shipper_order(order_id, otp, db, current_user, status=OrderStatus.Ongoing)
    
    order.order_status = OrderStatus.Deliverd
    db.commit()
    
    shipment.drop_order(order_id)
    return {"message": "Order delivered successfully"}
