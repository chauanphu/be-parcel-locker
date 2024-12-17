from datetime import date
import random
from typing import Optional, List
import uuid
from fastapi import APIRouter, Depends, Query, status, HTTPException
from pydantic import BaseModel, EmailStr
from auth.utils import get_current_user,check_admin
from sqlalchemy.orm import Session, joinedload
from models.account import Account
from database.session import get_db
from models.locker import Cell, Locker
from models.order import Order
from routers.parcel import Parcel 

from utils.mqtt import locker_client
from utils.redis import redis_client

from enum import Enum

from vrp_solver.solver import solve_vrp

router = APIRouter(
    prefix="/order",
    tags=["order"],
    dependencies=[Depends(get_current_user)]
)

class OrderStatusEnum(str, Enum):
    Packaging = 'Packaging'
    Ongoing = 'Ongoing'
    Waiting = 'Waiting'
    Delivered = 'Delivered'
    Completed = 'Completed'

class BaseParcel(BaseModel):
    width: int
    length: int
    height: int
    weight: int

class ParcelRead(BaseParcel):
    parcel_size: str

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
    recipient_phone: str
    sending_locker_id: int
    receiving_locker_id: int

class AddressResponse(BaseModel):
    addressName: str
    longitude: float
    latitude: float

class OrderResponse(BaseOrderInfo):
    order_id: int
    sender_id: int
    sender_information: BaseSenderInfo
    recipient_id: int
    sending_address: AddressResponse
    receiving_address: AddressResponse
    ordering_date: date
    sending_date: Optional[date]
    receiving_date: Optional[date]
    order_status: OrderStatusEnum
    parcel: ParcelRead

class OrderResponseSingle(BaseOrderInfo):
    order_id: int
    parcel: ParcelRead
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

class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[OrderResponse]

class PaginatedHistoryResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[OrderResponse]

# Return all order along with their parcel and locker
def join_order_parcel_cell(db: Session = Depends(get_db)):
    query = db.query(Order).options(joinedload(Order.parcel)).join(Parcel, Order.order_id == Parcel.parcel_id)
    return query

def find_available_cell(locker_id: int, size_option: str, db: Session) -> Optional[Cell]:
    """
    Finds an available cell using Redis for availability tracking
    """
    # 1. Get all cells used by orders that is not completed
    used_cells = set()
    orders = db.query(Order).filter(Order.order_status != OrderStatusEnum.Completed).all()
    used_cells.update(order.sending_cell_id for order in orders)
    used_cells.update(order.receiving_cell_id for order in orders)
    used_cells = list(used_cells)
    available_cell = db.query(Cell).filter(
        Cell.locker_id == locker_id,
        Cell.size == size_option,
        ~Cell.cell_id.in_(used_cells)
        ).first()
    if available_cell:
        return available_cell
    return None

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

async def update_order_status(order_id: int, order_status: OrderStatusEnum, db: Session):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.order_status = order_status
#tạo order
@router.post("/")
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
        # Find recipient by phone
        recipient = db.query(Account).filter(Account.phone == order.recipient_phone).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient not found")
        
        db.add(recipient)
        db.commit()
        db.refresh(recipient)
        new_order = Order(
            sender_id=current_user.user_id,
            recipient_id=recipient.user_id,
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

        sending_locker = db.query(Locker).filter(Locker.locker_id == sending_locker_id).first()
        receiving_locker = db.query(Locker).filter(Locker.locker_id == receiving_locker_id).first()
        if not sending_locker or not receiving_locker:
            raise HTTPException(status_code=404, detail="Locker not found")
        
        # Cache order data in Redis with string conversion for all values
        order_cache_data = {
            "sending_locker_id": sending_locker_id,
            "sending_latitude": sending_locker.latitude,
            "sending_longitude": sending_locker.longitude,
            "sending_cell_id": sending_cell.cell_id,
            "receiving_locker_id": receiving_locker_id,
            "receiving_latitude": receiving_locker.latitude,
            "receiving_longitude": receiving_locker.longitude,
            "receiving_cell_id": receiving_cell.cell_id,
            "status": OrderStatusEnum.Packaging.value,  # Convert enum to string
            "weight": parcel_data.weight,
            "size": size_option
        }
        pipeline.hmset(f"order:{new_order.order_id}", order_cache_data)
        pipeline.execute()

        return status.HTTP_201_CREATED

    except Exception as e:
        db.rollback()
        # Cleanup Redis if error occurs
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Handling cell unlock by POST request
@router.post("/generate_qr")
def unlock_cell(order_id: int, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    # Find the order_id
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if (order.order_status.value != OrderStatusEnum.Packaging.value) and (order.order_status.value != OrderStatusEnum.Delivered.value):
        raise HTTPException(status_code=400, detail="Invalid operation for current order status")
    # Determine whether sender or recipient is the current user
    is_sender = None
    if order.sender_id == current_user.user_id:
        is_sender = "sender"
    elif order.recipient_id == current_user.user_id:
        is_sender = "recipient"
    else:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    cache_order = redis_client.hgetall(f"order:{order_id}")
    if not cache_order:
        locker_id = cache_order.get("sending_locker_id") if is_sender == "sender" else cache_order.get("receiving_locker_id")
    else:
        target = order.sending_cell_id if is_sender == "sender" else order.receiving_cell_id
        locker = db.query(Locker).join(Cell).filter(Cell.cell_id == target).first()
        locker_id = locker.locker_id
        
    # Generate OTP code
    otp = random.randint(100000, 999999)
    redis_client.setex(f"otp:{order_id}", 60, otp)
    # TODO sending QR code to unlock the cell
    locker_client.print_qr(locker_id, order_id, code=otp)
    db.commit()
    return {"message": "QR code generated successfully"}

@router.post("/verify_qr")
async def verify_qr(order_id: int, otp: int, db: Session = Depends(get_db), current_user: Account = Depends(get_current_user)):
    # Find the order
    order_db = db.query(Order).filter(Order.order_id == order_id).first()
    if not order_db:
        raise HTTPException(status_code=404, detail="Order not found")
    # Determine whether sender or recipient is the current user
    is_sender = None
    if order_db.sender_id == current_user.user_id:
        is_sender = "sender"
    elif order_db.recipient_id == current_user.user_id:
        is_sender = "recipient"
    else:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # Get the cached order info
    order = redis_client.hgetall(f"order:{order_id}")
    if not order:
        raise HTTPException(status_code=404, detail="Order not found in cache")

    # Verify OTP
    stored_otp = redis_client.get(f"otp:{order_id}")
    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP code not found or expired")
    if int(stored_otp) != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Update status based on user role and current status
    status = order.get("status")
    if is_sender == "sender" and status == OrderStatusEnum.Packaging.value:
        await update_order_status(order_id, OrderStatusEnum.Waiting, db)
        # Update order.receiver_date
        db.query(Order).filter(Order.order_id == order_id).update({"sending_date": date.today()})
        redis_client.hset(f"order:{order_id}", "status", OrderStatusEnum.Waiting.value)
        target_cell_id = order.get("sending_cell_id")
        target_locker_id = order.get("sending_locker_id")
        solve_vrp()
        
    elif is_sender == "recipient" and status == OrderStatusEnum.Ongoing.value:
        await update_order_status(order_id, OrderStatusEnum.Completed, db)
        # Update order.receiver_date
        db.query(Order).filter(Order.order_id == order_id).update({"receiving_date": date.today()})
        target_cell_id = order.get("receiving_cell_id")
        target_locker_id = order.get("receiving_locker_id")
        redis_client.delete(f"order:{order_id}")
    else:
        raise HTTPException(status_code=400, detail="Invalid operation for current order status")

    # Unlock the appropriate cell
    locker_client.unlock(target_locker_id, target_cell_id)
    
    # Remove the OTP code from redis
    redis_client.delete(f"otp:{order_id}")
    db.commit()
    return {"message": "OTP verified successfully"}

#get order by paging
@router.get("/", response_model=PaginatedResponse, dependencies=[Depends(check_admin)])
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
        parcel = db.query(Parcel).filter(Parcel.parcel_id == order.order_id).first()
        sending_locker = find_locker_by_cell(order.sending_cell_id, db)
        receiving_locker = find_locker_by_cell(order.receiving_cell_id, db)
        # Create OrderResponse instance
        response = OrderResponse(
            order_id=order.order_id,
            sender_id=order.sender_id,
            sender_information=BaseSenderInfo(
                name = order.sender.name,
                phone = order.sender.phone,
                address = order.sender.address
            ),
            recipient_id = order.recipient_id,
            recipient_information = BaseSenderInfo(
                name = order.recipient.name,
                phone = order.recipient.phone,
                address = order.recipient.address
            ),
            sending_address = AddressResponse(
                addressName = sending_locker.address,
                longitude = sending_locker.longitude,
                latitude = sending_locker.latitude
            ),
            receiving_address = AddressResponse(
                addressName = receiving_locker.address,
                longitude = receiving_locker.longitude,
                latitude = receiving_locker.latitude
            ),
            ordering_date=order.ordering_date,
            sending_date=order.sending_date,
            receiving_date=order.receiving_date,
            order_status=order.order_status,
            parcel = ParcelRead(
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
    parcel = db.query(Parcel).filter(Parcel.parcel_id == order.order_id).first()

    # Extract and convert data
    sending_locker = find_locker_by_cell(order.sending_cell_id, db)
    receiving_locker = find_locker_by_cell(order.receiving_cell_id, db)

    sender_info = BaseSenderInfo(
        name=order.sender.name,
        phone=order.sender.phone,
        address=order.sender.address
    )
    
    parcel_info = ParcelRead(
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

# #update order status by order id
# @router.put(
#     "/{order_id}",
#     summary="Update order status",
#     )
# async def update_order_status(order_id: int, order_status: OrderStatusEnum, db: Session = Depends(get_db)):
#     # First, find the order by order_id
#     existing_order = db.query(Order).filter(Order.order_id == order_id).first()
    
#     if existing_order is None:
#         raise HTTPException(status_code=404, detail="Order not found")
    
#     # Check the current order status
#     if existing_order.order_status != OrderStatusEnum.Packaging:
#         return HTTPException(status_code=400, detail="Order status cannot be updated")
    
#     # Update the order status to "Canceled"
#     existing_order.order_status = OrderStatusEnum.Canceled
    
#     # Update other fields if necessary
#     for field, value in order_status.model_dump(exclude_unset=True, exclude_none=True).items():
#         setattr(existing_order, field, value)
    
#     # Commit the changes to the database
#     db.commit()
    
#     return {"Message": f"Order_id {order_id} is canceled"}

#delete order bằng parcel_id
@router.delete("/{order_id}", dependencies=[Depends(check_admin)])
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order_delete = db.query(Order).filter(Order.order_id == order_id).first()
    #nếu order không được tìm thấy thì là not found
    if not order_delete:
        raise HTTPException(status_code=404, detail="Order not found")
        # Delete order from Redis cache first
    redis_client.delete(f"order:{order_id}")
    redis_client.delete(f"otp:{order_id}")  # Also clean up any lingering OTP
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
@router.get("/history/", response_model=PaginatedHistoryResponse)
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
        parcel = db.query(Parcel).filter(Parcel.parcel_id == order.order_id).first()
        sending_locker = find_locker_by_cell(order.sending_cell_id, db)
        receiving_locker = find_locker_by_cell(order.receiving_cell_id, db)
        if not sending_locker or not receiving_locker:
            raise HTTPException(status_code=404, detail="Locker not found")
        if not parcel:
            raise HTTPException(status_code=404, detail="Parcel not found")
        # Create OrderResponse instance
        response = OrderResponse(
            order_id=order.order_id,
            sender_id=order.sender_id,
            sender_information=BaseSenderInfo(
                name=order.sender.name,
                phone=order.sender.phone,
                address=order.sender.address
            ),
            recipient_id=order.recipient_id,
            recipient_information=BaseSenderInfo(
                name=order.recipient.name,
                phone=order.recipient.phone,
                address=order.recipient.address
            ),
            sending_address=AddressResponse(
                addressName=sending_locker.address,
                longitude=sending_locker.longitude,
                latitude=sending_locker.latitude
            ),
            receiving_address=AddressResponse(
                addressName=receiving_locker.address,
                longitude=receiving_locker.longitude,
                latitude=receiving_locker.latitude
            ),
            ordering_date=order.ordering_date,
            sending_date=order.sending_date,
            receiving_date=order.receiving_date,
            order_status=order.order_status,
            parcel=ParcelRead(
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
