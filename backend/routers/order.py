from datetime import date
import logging
import random
from typing import Any, Dict, List, Optional
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
from routers.parcel import ParcelRequest, Parcel 
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
    
class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatusEnum
    
class ParcelResponse(BaseModel):
    width: int
    length: int
    height: int
    weight: int
    parcel_size: str

class ParcelRequest(BaseModel):
    length: int
    width: int
    height: int
    weight: int
    # parcel_size: str

class RecipientRequest(BaseModel):
    email: EmailStr
    name: str
    phone: str
    
class OrderRequest(BaseModel):
    parcel: Optional[ParcelRequest]
    # sender_id: int
    recipient_id: Optional[RecipientRequest]
    sending_locker_id: Optional[int]
    receiving_locker_id: Optional[int]
    
class sender_informations(BaseModel):
    name : Optional[str]
    phone : Optional[str]
    address : Optional[str]

class OrderResponse(BaseModel):
    order_id: int
    parcel: ParcelResponse
    sender_id: int
    sender_informations: sender_informations
    recipient_id: int
    sending_address: str
    receiving_address: str
    ordering_date:date
    sending_date: Optional[date] 
    receiving_date: Optional[date]
    order_status: OrderStatusEnum
    # warnings: bool

class OrderResponseFor1Order(BaseModel):
    order_id: int
    parcel: ParcelResponse
    sender_informations: sender_informations
    sending_address: str
    receiving_address: str
    ordering_date:date
    sending_date: Optional[date] 
    receiving_date: Optional[date]
    order_status: OrderStatusEnum

class OrderStatus(BaseModel):
    order_status: OrderStatusEnum

class Token2(BaseModel):
    order_id: int
    message: str
    parcel_size: str
    sender_id: int  # Add sender_id here

class CompletedOrderResponse(BaseModel):
    order_id: int
    recipient_id: int   
    sending_date: Optional[date]
    receiving_date: Optional[date]
    order_status: str

# Return all order along with their parcel and locker
def join_order_parcel_cell(db: Session = Depends(get_db)):
    query = db.query(Order).options(joinedload(Order.parcel)).join(Parcel, Order.order_id == Parcel.parcel_id)
    return query

def find_available_cell(locker_id: int, size_options: List[str], db: Session):
    """
    Finds an available cell in the specified locker.

    Parameters:
    - locker_id (int): The ID of the locker to search for available cells.
    - db (Session): The database session to use for the query.

    Returns:
    - Cell: The first available cell found in the locker, or None if no available cells are found.
    """
    cell = db.query(Cell).filter(
        Cell.locker_id == locker_id,
        Cell.size.in_(size_options),
        Cell.occupied == False
    ).first()
    if cell:
        return cell, cell.size   
    # Return (None, None) if no cell is found for any of the sizes
    return None, None

def change_cell_occupied(cell_id: uuid, occupied: bool, db: Session):
    """
    Changes the occupied status of the specified cell.
    Parameters:
    - cell_id (uuid): The ID of the cell to change the status of.
    - occupied (bool): The new occupied status of the cell.
    - db (Session): The database session to use for the query.

    Returns:
    - Cell: The updated cell.
    """
    cell = db.query(Cell).filter(Cell.cell_id == cell_id).first()
    if cell:
        logging.debug(f"Changing cell {cell_id} occupied status to {occupied}")
        cell.occupied = occupied
        db.commit()
    else:
        logging.error(f"Cell with id {cell_id} not found")

def find_locker_by_cell(cell_id: uuid, db: Session = Depends(get_db)):
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

def to_dict(model_instance):
    data = model_instance.__dict__.copy()
    data.pop('_sa_instance_state', None)
    return data

def determine_parcel_size(length: int, width: int, height: int, weight: int) -> List[str]:
    size_options = []
    if length*width*height <= 13*15*30:     #lenght is 13, widht is 15, height is 30
        size_options.append("S")
    if length*width*height <= 23*15*30:     #lenght is 23, widht is 15, height is 30
        size_options.append("M")
    if length*width*height <= 33*20*30:     #lenght is 33, widht is 20, height is 30
        size_options.append("L")
    if not size_options:
        raise HTTPException(status_code=400, detail="Parcel dimensions exceed all available sizes")
    return size_options
 
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
            return recipient.recipient_id
        else:
            return recipient_query.recipient_id
        
    #if the user already in the database, create a recipient with that user_id 
    profile = db.query(Profile).filter(Profile.user_id == user.user_id).first()
    user_recipient = Recipient(
        name = profile.name,
        phone = profile.phone,
        email = user.email,
        profile_id = profile.user_id
    )
    db.add(user_recipient)
    db.commit()
    return user_recipient.recipient_id

#tạo order
@router.post("/", response_model=Token2) 
def create_order(order: OrderRequest, 
                 db: Session = Depends(get_db),
                 current_user: Account = Depends(get_current_user)):
    try:
        # Convert order to dict and remove the parcel
        new_order_data = order.dict(exclude_none=True, exclude_unset=True)
        parcel_data = new_order_data.pop('parcel')
        sending_locker_id = new_order_data.pop('sending_locker_id')
        receiving_locker_id = new_order_data.pop('receiving_locker_id')

        # Determine parcel size based on dimensions and weight
        size_options = determine_parcel_size(parcel_data['length'], parcel_data['width'], parcel_data['height'], parcel_data['weight'])

        # Query the available cell in the sending locker
        sending_cell, final_size = find_available_cell(sending_locker_id, size_options, db)
        if not sending_cell:
            raise HTTPException(status_code=400, detail="No available cells in the sending locker")
        
        logging.debug(f"Found sending cell: {sending_cell.cell_id}")
        change_cell_occupied(sending_cell.cell_id, True, db)
  
       # Query the available cell in the receiving locker
        receiving_cell, _ = find_available_cell(receiving_locker_id, [final_size], db)
        if not receiving_cell:
            # Free up the sending cell if the receiving cell is not available
            change_cell_occupied(sending_cell.cell_id, False, db)
            raise HTTPException(status_code=400, detail="No available cells in the receiving locker")
        
        logging.debug(f"Found receiving cell: {receiving_cell.cell_id}")
        change_cell_occupied(receiving_cell.cell_id, True, db)
        
        # Get recipient_id based on recipient information
        recipient_data = order.recipient_id
        recipient_id = get_user_id_by_recipient_info(db, recipient_data.email, recipient_data.phone, recipient_data.name)
        
         # Add sender_id to order data
        new_order_data['sender_id'] = current_user.user_id
        new_order_data['recipient_id'] = recipient_id

        # Update the order with the cell IDs
        new_order_data['sending_cell_id'] = sending_cell.cell_id
        new_order_data['receiving_cell_id'] = receiving_cell.cell_id
        new_order = Order(**new_order_data)
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # Create the parcel record
        parcel_data['parcel_size'] = final_size
        parcel_data['parcel_id'] = new_order.order_id
        new_parcel = Parcel(**parcel_data)
        db.add(new_parcel)
        db.commit()
        
        # Convert cell_id to string for Redis
        order_id = str(new_order.order_id)
        sending_cell_id = str(sending_cell.cell_id)
        receiving_cell_id = str(receiving_cell.cell_id)
        receiving_locker_id = str(receiving_locker_id)
        sending_locker_id = str(sending_locker_id)

        # Save the order data to Redis
        redis_client.hmset(f"order:{order_id}", {
            "sending_locker_id": sending_locker_id,
            "receiving_locker_id": receiving_locker_id,
            "sending_cell_id": sending_cell_id,
            "receiving_cell_id": receiving_cell_id
        })

        # Return the newly created order with the parcel size for OrderResponse
        return {
            "order_id": new_order.order_id,
            "message": 'Successfully created',
            "parcel_size": final_size,
            "sender_id": current_user.user_id  

        }
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Handling cell unlock by POST request
@router.post("/generate_qr")
def unlock_cell(order_id: int, db: Session = Depends(get_db)):  
    # Find the order_id
    order = redis_client.hgetall(f"order:{order_id}")

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Find the locker_id
    locker_id = order.get("sending_locker_id")
    # Generate OTP code
    otp = random.randint(100000, 999999)
    redis_client.setex(f"otp:{order_id}", 300, otp)
    # TODO sending QR code to unlock the cell
    locker_client.print_qr(locker_id, order_id, code=otp)
    db.commit()
    return {"message": "QR code generated successfully"}

@router.post("/verify_qr")
def verify_order(order_id: int, otp: int, db: Session = Depends(get_db)):
    # Find the order_id in the redis
    order = redis_client.hgetall(f"order:{order_id}")
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Get the OTP code from redis
    stored_otp = redis_client.get(f"otp:{order_id}")
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
            sender_informations=sender_informations(
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
            parcel = ParcelResponse(
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
@router.get("/{order_id}", response_model=OrderResponseFor1Order)
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
  
    
    
    sender_info = sender_informations(
        name=profile.name if profile else "",
        phone=profile.phone if profile else "",
        address=profile.address if profile else ""
    )
    
    parcel_info = ParcelResponse(
            width = parcel.width,
            length = parcel.length,
            height = parcel.height,
            weight = parcel.weight,
            parcel_size = parcel.parcel_size
    )
    response = OrderResponseFor1Order(
        order_id=order.order_id,
        sender_informations=sender_info,
        sending_address= sending_locker.address,
        receiving_address= receiving_locker.address,
        ordering_date=order.ordering_date,
        sending_date=order.sending_date,
        receiving_date=order.receiving_date,
        order_status=order.order_status,
        parcel = parcel_info
    )
    
    return response

#update order by parcel_id    
@router.patch("/{order_id}", response_model=OrderRequest)
def update_package(order_id: int, _package: OrderRequest, db: Session = Depends(get_db)):
    # Allow for partial updates
    package_put = db.query(Order).filter(Order.order_id == order_id).update(
        _package.model_dump(
            exclude_unset=True, 
            exclude_none=True
        ))
    # Check if order exists
    # If not, raise an error
    if not package_put:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.commit()
    return package_put

#update order status by order id
@router.put("/{order_id}/update_order_status")
async def update_order_status(order_id: int, order: OrderStatus, db: Session = Depends(get_db)):
    # First, find the order by order_id
    existing_order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if existing_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check the current order status
    if existing_order.order_status != "Packaging":
        return {"Message": f"You can only cancel when Packaging"}
    
    # Update the order status to "Canceled"
    existing_order.order_status = "Canceled"
    
    # Update other fields if necessary
    for field, value in order.model_dump(exclude_unset=True, exclude_none=True).items():
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
    #nếu xóa rồi mà quên xong xóa thêm lần nữa thì hiện ra là k tồn tại
    if order_delete == None:
        raise HTTPException(status_code=404, detail="Order not exist")
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

# # Get cell
# @router.get("/{locker_id}/{parcel_id}", response_model=OrderRequest)
# def get_cell(locker_id: str, parcel_id: int, db: Session = Depends(get_db)):
#     package = db.query(Order).filter(Order.locker_id == locker_id).filter(Order.parcel_id == parcel_id).first()
#     if not package:
#         raise HTTPException(status_code=404, detail="Order not found")
#     return package



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
            sender_informations=sender_informations(
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
            parcel=ParcelResponse(
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
