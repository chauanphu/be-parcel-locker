import random
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, EmailStr, Field
from models.account import Account
from models.locker import Cell, Locker
from models.role import Role
from models.order import Order, OrderStatus
from database.session import get_db
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, List
from auth.utils import get_current_user, hash_password

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

class ShipperResponse(BaseModel):
    shipper_id: int
    name: str
    gender: Optional[str]
    age: Optional[int]
    phone: Optional[str]
    address: Optional[str]

class PaginatedShipperResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[ShipperResponse]

#GET PAGING SHIPPER
@router.get("/", response_model=PaginatedShipperResponse)
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

    # Format the response using the Pydantic model
    shipper_responses = [
        ShipperResponse(
            shipper_id=shipper.user_id,
            name=shipper.name,
            gender=shipper.gender,
            age=shipper.age,
            phone=shipper.phone,
            address=shipper.address,
        )
        for shipper in shippers
    ]

    total_pages = (total_shippers + per_page - 1) // per_page
    return PaginatedShipperResponse(
        total=total_shippers,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        data=shipper_responses
    )

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
def verify_shipper_order(order_id: int, otp: int, db: Session, current_user: Account, _status: OrderStatus = None) -> Order:
    """Common verification function for shipper operations"""
    if current_user.role_rel.name != "shipper":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only shippers can perform this action")
    
    if not _status:
        order: Order = db.query(Order).filter(
            Order.order_id == order_id, 
            Order.shipper_id == current_user.user_id
        ).first()
    else:
        order: Order = db.query(Order).filter(
            Order.order_id == order_id, 
            Order.shipper_id == current_user.user_id,
            Order.order_status == _status
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
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if (order.order_status != OrderStatus.Waiting) and (order.order_status != OrderStatus.Ongoing):
        raise HTTPException(status_code=400, detail="Invalid order status")
    
    cache_order = redis_client.hgetall(f"order:{order_id}")
    
    if cache_order["status"] == "Waiting":
        locker_id = cache_order["sending_locker_id"]
    elif cache_order["status"] == "Ongoing":
        locker_id = cache_order["receiving_locker_id"]
    else:
        raise HTTPException(status_code=400, detail="Invalid order status")
    
    # Generate OTP code
    otp = random.randint(100000, 999999)
    redis_client.setex(f"otp:{order_id}", 60, otp)
    # TODO sending QR code to unlock the cell
    locker_client.print_qr(locker_id, order_id, code=otp)
    db.commit()
    return {"message": "QR code generated successfully"}

@router.post("/pickup/{order_id}")
def pickup_order(order_id: int, otp: int, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    if otp is None:
        raise HTTPException(status_code=400, detail="OTP code is required")
    order = verify_shipper_order(order_id, otp, db, current_user, _status=OrderStatus.Waiting)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.order_status != OrderStatus.Waiting:
        raise HTTPException(status_code=400, detail="Invalid order status")
    
    
    order.order_status = OrderStatus.Ongoing
    # Update the order status
    redis_client.hset(f"order:{order_id}", "status", "Ongoing")
    db.commit()
    
    target_locker_id = redis_client.hget(f"order:{order_id}", "sending_locker_id")
    target_cell_id = redis_client.hget(f"order:{order_id}", "sending_cell_id")
    locker_client.unlock(target_locker_id, target_cell_id)
    shipment.pickup_order(order_id)
        # Unlock the appropriate cell

    return {"message": "Order picked up successfully"}

@router.post("/deliver/{order_id}")
def deliver_order(order_id: int, otp: int, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    if otp is None:
        raise HTTPException(status_code=400, detail="OTP code is required")
    order = verify_shipper_order(order_id, otp, db, current_user, _status=OrderStatus.Ongoing)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.order_status != OrderStatus.Ongoing:
        raise HTTPException(status_code=400, detail="Invalid order status")
    
    order.order_status = OrderStatus.Delivered
    redis_client.hset(f"order:{order_id}", "status", "Delivered")
    db.commit()
    target_locker_id = redis_client.hget(f"order:{order_id}", "receiving_locker_id")
    target_cell_id = redis_client.hget(f"order:{order_id}", "receiving_cell_id")
    locker_client.unlock(target_locker_id, target_cell_id)
    shipment.drop_order(order_id)
        # Unlock the appropriate cell

    return {"message": "Order delivered successfully"}
