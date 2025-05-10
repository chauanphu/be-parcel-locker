from datetime import date
import logging
import random
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
from fastapi import APIRouter, Depends, Query
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from auth.utils import get_current_user,check_admin
from sqlalchemy.orm import Session, joinedload
from models.account import Account
from models.recipient import Recipient
from database.session import get_db
from models.locker import Cell, Locker
from models.order import Order
from routers.parcel import Parcel 
from models.profile import Profile

from utils.mqtt import locker_client
from utils.redis import redis_client

from enum import Enum

router = APIRouter(
    prefix="/order",
    tags=["order"],
    dependencies=[Depends(get_current_user)]
)

class OrderStatusEnum(str, Enum):
    Completed = "Completed"
    Canceled = "Canceled"
    Ongoing = "Ongoing"
    Delayed = "Delayed"
    Expired = "Expired"
    Packaging = "Packaging"

class BaseParcel(BaseModel):
    width: int
    length: int
    height: int
    weight: int
    parcel_size: Optional[str] = None

class BaseOrderInfo(BaseModel):
    sending_address: str
    receiving_address: str
    ordering_date: date
    sending_date: Optional[date]
    receiving_date: Optional[date]
    order_status: OrderStatusEnum

class BaseSenderInfo(BaseModel):
    name: Optional[str]
    phone: Optional[str]
    address: Optional[str]

class UpdateOrderStatus(BaseModel):
    status: OrderStatusEnum

class RecipientInfo(BaseModel):
    email: EmailStr
    name: str
    phone: str

class OrderCreate(BaseModel):
    parcel: BaseParcel
    recipient: RecipientInfo
    sending_locker_id: int
    receiving_locker_id: int

class OrderResponse(BaseOrderInfo):
    order_id: int
    parcel: BaseParcel
    sender_id: int
    sender_information: BaseSenderInfo
    recipient_id: int

class OrderResponseSingle(BaseOrderInfo):
    order_id: int
    parcel: BaseParcel
    sender_information: BaseSenderInfo

class OrderStatus(BaseModel):
    order_status: OrderStatusEnum

class OrderActionResponse(BaseModel):
    order_id: int
    message: str
    parcel_size: str
    sender_id: int

class CompletedOrder(BaseModel):
    order_id: int
    recipient_id: int   
    sending_date: Optional[date]
    receiving_date: Optional[date]
    order_status: str

# Return all order along with their parcel and locker
def join_order_parcel_cell(db: Session = Depends(get_db)):
    query = db.query(Order).options(joinedload(Order.parcel)).join(Parcel, Order.order_id == Parcel.parcel_id)
    return query

def find_available_cell(locker_id: int, size_option: str, db: Session) -> Union[Tuple[Cell, str], Tuple[None, None]]:
    """
    Finds an available cell using Redis for availability tracking
    """
    # 1. Get all cells used by orders that is not completed
    used_cells = set()
    orders = db.query(Order).filter(Order.order_status != OrderStatusEnum.Completed).all()
    used_cells.update(order.sending_cell_id for order in orders)
    used_cells.update(order.receiving_cell_id for order in orders)

    available_cell = db.query(Cell).filter(
        Cell.locker_id == locker_id,
        Cell.size == size_option,
        Cell.cell_id.notin_(used_cells)
        ).first()
    if available_cell:
        return available_cell
    return None, None

def find_locker_by_cell(cell_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Finds the locker that contains the specified cell.

    Parameters:
    - cell_id (uuid): The ID of the cell to find the locker for.
    - db (Session): The database session to use for the query.

    Returns:
    - Locker: The locker that contains the specified cell.
    """
    query = db.query(Locker).filter(Locker.cells.any(Cell.cell_id == cell_id)).first()
    return query

class Size:
    def __init__(self, width: float, length: float, height: float, weight: float):
        self.width = width
        self.length = length
        self.height = height
        self.weight = weight

    def isFit(self, width: float, length: float, height: float, weight: float):
        return self.width >= width and self.length >= length and self.height >= height and self.weight >= weight

# Define the available parcel sizes: S, M, L
# Width, length, height, weight
SizeS = Size(13, 15, 30, 5)
SizeM = Size(23, 15, 30, 10)
SizeL = Size(33, 20, 30, 15)

def determine_parcel_size(length: int, width: int, height: int, weight: int) -> str:
    if SizeS.isFit(width, length, height, weight):
        return "S"
    if SizeM.isFit(width, length, height, weight):
        return "M"
    if SizeL.isFit(width, length, height, weight):
        return "L"
    raise HTTPException(status_code=400, detail="Parcel dimensions exceed all available sizes")

def get_user_id_by_recipient_info(db: Session, email: str, phone: str, name: str) -> int:
    # Query the user by email
    user = db.query(Account).filter(Account.email == email).first()
    
    if user is None:
        recipient_query = db.query(Recipient).filter(Recipient.phone == phone).first()
        if recipient_query is None:
            #Then the profile_id of the recipient is null and save a new recipient
            recipient = Recipient(
                name = name,
                phone = phone, 
                email = email
            )
            db.add(recipient)
            db.commit()
            return recipient.recipient_id.value
        else:
            return recipient_query.recipient_id.value
        
    #if the user already in the database, create a recipient with that user_id 
    profile = db.query(Profile).filter(Profile.user_id == user.user_id).first()
    if profile is None:
        raise HTTPException(status_code=400, detail="User profile not found")
    user_recipient = Recipient(
        name = profile.name,
        phone = profile.phone,
        email = user.email,
        profile_id = profile.user_id
    )
    db.add(user_recipient)
    db.commit()
    return user_recipient.recipient_id.value

#tạo order
@router.post("/", response_model=OrderActionResponse)
def create_order(order: OrderCreate, 
                 db: Session = Depends(get_db),
                 current_user: Account = Depends(get_current_user)):
    sending_cell = None
    receiving_cell = None
    pipeline = None
    
    try:
        parcel_data = order.parcel
        sending_locker_id = order.sending_locker_id
        receiving_locker_id = order.receiving_locker_id

        size_option = determine_parcel_size(
            parcel_data.length, 
            parcel_data.width, 
            parcel_data.height, 
            parcel_data.weight
        )

        # Start Redis transaction
        pipeline = redis_client.pipeline()

        sending_cell: Cell = find_available_cell(sending_locker_id, size_option, db)
        receiving_cell: Cell = find_available_cell(receiving_locker_id, size_option, db)

        if not sending_cell:
            raise HTTPException(status_code=400, detail="No available cells in sending locker")
        if not receiving_cell:
            raise HTTPException(status_code=400, detail="No available cells in receiving locker")
        new_recipient = Recipient(
            email = order.recipient.email,
            name = order.recipient.name,
            phone = order.recipient.phone
        )
        db.add(new_recipient)
        db.commit()
        db.refresh(new_recipient)
        new_order = Order(
            sender_id=current_user.user_id,
            recipient_id=new_recipient.recipient_id,
            sending_cell_id=sending_cell.cell_id,
            receiving_cell_id=receiving_cell.cell_id,
            order_status=OrderStatusEnum.Packaging
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        new_parcel = Parcel(
            parcel_id=new_order.order_id,
            width=parcel_data.width, 
            length=parcel_data.length, 
            height=parcel_data.height, 
            weight=parcel_data.weight, 
            parcel_size=size_option
            )
        db.add(new_parcel)
        db.commit()

        # Cache order data in Redis with string conversion for all values
        order_cache_data = {
            "sending_locker_id": sending_locker_id,
            "receiving_locker_id": receiving_locker_id,
            "sending_cell_id": str(sending_cell.cell_id),
            "receiving_cell_id": str(receiving_cell.cell_id),
            "status": OrderStatusEnum.Packaging.value,  # Convert enum to string
            "latitude": 0.0,
            "longitude": 0.0,
        }
        pipeline.hmset(f"order:{new_order.order_id}", order_cache_data)
        pipeline.execute()

        return OrderActionResponse(
            order_id=new_order.order_id,
            message="Order created successfully",
            parcel_size=size_option,
            sender_id=current_user.user_id
        )

    except Exception as e:
        db.rollback()
        # Cleanup Redis if error occurs
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Handling cell unlock by POST request
@router.post("/generate_qr")
def unlock_cell(order_id: int, db: Session = Depends(get_db)):  
    # Find the order_id
    order = redis_client.hgetall(f"order:{order_id}")

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Find the locker_id
    locker_id = order[b"sending_locker_id"].decode("utf-8")
    # Generate OTP code
    otp = random.randint(100000, 999999)
    redis_client.setex(f"otp:{order_id}", 300, otp)
    # TODO sending QR code to unlock the cell
    locker_client.print_qr(locker_id, order_id, code=otp)
    db.commit()
    return {"message": "QR code generated successfully"}

@router.post("/verify_qr")
async def verify_order(order_id: int, otp: int, db: Session = Depends(get_db)):
    # Find the order_id in the redis
    order = redis_client.hgetall(f"order:{order_id}")
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Get the OTP code from redis
    stored_otp = await redis_client.get(f"otp:{order_id}")
    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP code not found or expired")
    if int(stored_otp) != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    # Get sending locker and cell from redis
    sending_locker_id = order.get("sending_locker_id")
    sending_cell_id = order.get("sending_cell_id")
    # Send request to unlock the cell
    locker_client.unlock(sending_locker_id, sending_cell_id)
    # Remove the OTP code from redis
    redis_client.delete(f"otp:{order_id}")
    return {"message": "OTP verified successfully"}

#get order by paging
@router.get("/",response_model=Dict[str, Any], dependencies=[Depends(check_admin)])
async def get_paging_order(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),  # Current page number for lockers
    per_page: int = Query(10, ge=1),  # Number of lockers per page
):
    
    # Calculate the total number of orders
    total_orders = db.query(Order).count()

    # Fetch paginated list of orders
    orders = db.query(Order).offset((page - 1) * per_page).limit(per_page).all()
    order_responses = []
    for order in orders:
        # Fetch sender profile
        profile = db.query(Profile).filter(Profile.user_id == order.sender_id).first()
        parcel = db.query(Parcel).filter(Parcel.parcel_id == order.order_id).first()
        sending_locker = find_locker_by_cell(order.sending_cell_id, db)
        receiving_locker = find_locker_by_cell(order.receiving_cell_id, db)
        # Create OrderResponse instance
        response = OrderResponse(
            order_id=order.order_id,
            sender_id=order.sender_id,
            sender_information=BaseSenderInfo(
                name = profile.name if profile else "",
                phone = profile.phone if profile else "",
                address = profile.address if profile else ""
            ),
            recipient_id = order.recipient_id,
            sending_address = sending_locker.address,
            receiving_address = receiving_locker.address,
            ordering_date=order.ordering_date,
            sending_date=order.sending_date,
            receiving_date=order.receiving_date,
            order_status=order.order_status,
            parcel = BaseParcel(
            width = parcel.width,
            length = parcel.length,
            height = parcel.height,
            weight = parcel.weight,
            parcel_size = parcel.parcel_size
    )
        )
        order_responses.append(response) 
    total_pages = (total_orders + per_page - 1) // per_page
    return {
        "total": total_orders,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": order_responses
    }

#GET order bằng order_id
@router.get("/{order_id}", response_model=OrderResponseSingle)
def get_order(order_id: int, db: Session = Depends(get_db)):
    query = join_order_parcel_cell(db)
    order = query.filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    profile = db.query(Profile).filter(Profile.user_id == order.sender_id).first()
    parcel = db.query(Parcel).filter(Parcel.parcel_id == order.order_id).first()

    # Extract and convert data
    sending_locker = find_locker_by_cell(order.sending_cell_id, db)
    receiving_locker = find_locker_by_cell(order.receiving_cell_id, db)

    sender_info = BaseSenderInfo(
        name=profile.name if profile else "",
        phone=profile.phone if profile else "",
        address=profile.address if profile else ""
    )
    
    parcel_info = BaseParcel(
            width = parcel.width,
            length = parcel.length,
            height = parcel.height,
            weight = parcel.weight,
            parcel_size = parcel.parcel_size
    )
    response = OrderResponseSingle(
        order_id=order.order_id,
        sender_information=sender_info,
        sending_address= sending_locker.address,
        receiving_address= receiving_locker.address,
        ordering_date=order.ordering_date,
        sending_date=order.sending_date,
        receiving_date=order.receiving_date,
        order_status=order.order_status,
        parcel = parcel_info
    )
    
    return response

#update order status by order id
@router.put(
    "/{order_id}",
    summary="Update order status",
    )
async def update_order_status(order_id: int, order_status: OrderStatusEnum, db: Session = Depends(get_db)):
    # First, find the order by order_id
    existing_order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if existing_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check the current order status
    if existing_order.order_status != OrderStatusEnum.Packaging:
        return HTTPException(status_code=400, detail="Order status cannot be updated")
    
    # Update the order status to "Canceled"
    existing_order.order_status = OrderStatusEnum.Canceled
    
    # Update other fields if necessary
    for field, value in order_status.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(existing_order, field, value)
    
    # Commit the changes to the database
    db.commit()
    
    return {"Message": f"Order_id {order_id} is canceled"}

#delete order bằng parcel_id
@router.delete("/{order_id}", dependencies=[Depends(check_admin)])
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order_delete = db.query(Order).filter(Order.order_id == order_id).first()
    #nếu order không được tìm thấy thì là not found
    if not order_delete:
        raise HTTPException(status_code=404, detail="Order not found")
    parcel_to_delete = db.query(Parcel).filter(Parcel.parcel_id == order_delete.order_id).first()
    if parcel_to_delete:
        db.delete(parcel_to_delete)
    cells_sending = db.query(Cell).filter(Cell.cell_id == order_delete.sending_cell_id).update({"occupied": False})
    cells_recieved = db.query(Cell).filter(Cell.cell_id == order_delete.receiving_cell_id).update({"occupied": False})
    if (cells_recieved != 1) or (cells_sending != 1):
        raise HTTPException(status_code=404, detail=f"Cell not found, received:{cells_recieved}, sending:{cells_sending} ")
    db.delete(order_delete)
    db.commit()
    
    return {
        "Message": f"Order {order_id} deleted"
    }

#get histoy order by paging
@router.get("/history/order", response_model=Dict[str, Any])
async def get_history_order(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_user),  # Get the current authenticated user
    page: int = Query(1, ge=1),  # Current page number for orders
    per_page: int = Query(10, ge=1),  # Number of orders per page
):
    # Filter orders by sender_id (current user)
    query = db.query(Order).filter(Order.sender_id == current_user.user_id)
    
    # Calculate the total number of orders for the current user
    total_orders = query.count()

    # Fetch paginated list of orders
    orders = query.offset((page - 1) * per_page).limit(per_page).all()
    order_responses = []
    for order in orders:
        # Fetch sender profile
        profile = db.query(Profile).filter(Profile.user_id == order.sender_id).first()
        parcel = db.query(Parcel).filter(Parcel.parcel_id == order.order_id).first()
        sending_locker = find_locker_by_cell(order.sending_cell_id, db)
        receiving_locker = find_locker_by_cell(order.receiving_cell_id, db)
        
        # Create OrderResponse instance
        response = OrderResponse(
            order_id=order.order_id,
            sender_id=order.sender_id,
            sender_information=BaseSenderInfo(
                name=profile.name if profile else "",
                phone=profile.phone if profile else "",
                address=profile.address if profile else ""
            ),
            recipient_id=order.recipient_id,
            sending_address=sending_locker.address,
            receiving_address=receiving_locker.address,
            ordering_date=order.ordering_date,
            sending_date=order.sending_date,
            receiving_date=order.receiving_date,
            order_status=order.order_status,
            parcel=BaseParcel(
                width=parcel.width,
                length=parcel.length,
                height=parcel.height,
                weight=parcel.weight,
                parcel_size=parcel.parcel_size
            )
        )
        order_responses.append(response)
    
    # Calculate the total number of pages
    total_pages = (total_orders + per_page - 1) // per_page
    
    return {
        "total": total_orders,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": order_responses
    }
