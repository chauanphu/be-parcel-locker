from datetime import date, datetime
import logging
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from auth.utils import get_current_user
from sqlalchemy.orm import Session, joinedload, aliased
# from models.user import User
from models.shipper import Shipper
from models.account import Account
from database.session import get_db
from models.locker import Cell, Locker
from models.order import Order
from routers.locker import LockerInfoResponse
from routers.parcel import ParcelRequest, Parcel 
from models.profile import Profile
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
    parcel: ParcelRequest
    # sender_id: int
    recipient_id: RecipientRequest
    sending_locker_id: int
    receiving_locker_id: int
    

    
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
    sending_locker: int
    receiving_locker: int
    ordering_date:date
    sending_date: Optional[date] 
    receiving_date: Optional[date]
    order_status: OrderStatusEnum
    # warnings: bool

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

def find_available_cell(locker_id: int, size_options: List[str], db: Session = Depends(get_db)):
    """
    Finds an available cell in the specified locker.

    Parameters:
    - locker_id (int): The ID of the locker to search for available cells.
    - db (Session): The database session to use for the query.

    Returns:
    - Cell: The first available cell found in the locker, or None if no available cells are found.
    """
    for size in size_options:
        cell = db.query(Cell).filter(
            Cell.locker_id == locker_id,
            Cell.size == size,
            Cell.occupied == False
        ).first()
        if cell:
            return cell, size
    return None, None

def change_cell_occupied(cell_id: uuid, occupied: bool, db: Session = Depends(get_db)):
    """
    Changes the occupied status of the specified cell.
    Parameters:
    - cell_id (uuid): The ID of the cell to change the status of.
    - occupied (bool): The new occupied status of the cell.
    - db (Session): The database session to use for the query.

    Returns:
    - Cell: The updated cell.
    """
    query = db.query(Cell).filter(Cell.cell_id == cell_id).update({"occupied": occupied})
    db.commit()
    return query

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

def replace_cell_with_locer(order: Order, db: Session = Depends(get_db)):
    """
    Replaces the sending and receiving cell IDs in the order with the sending and receiving locker IDs.

    Parameters:
    - order (Order): The order to update.
    - db (Session): The database session to use for the query.

    Returns:
    - Order: The updated order.
    """
    query = db.query(Order).filter(Order.order_id == order.order_id).first()
    sending_locker = find_locker_by_cell(order.sending_cell_id, db)
    receiving_locker = find_locker_by_cell(order.receiving_cell_id, db)
    order.sending_locker_id = sending_locker.locker_id
    order.receiving_locker_id = receiving_locker.locker_id
    return order

def to_dict(model_instance):
    data = model_instance.__dict__.copy()
    data.pop('_sa_instance_state', None)
    return data

def determine_parcel_size(length: int, width: int, height: int, weight: int) -> List[str]:
    size_options = []
    if length <= 13 and width <= 15 and height <= 30 and weight <= 20:
        size_options.append("S")
    if length <= 23 and width <= 15 and height <= 30 and weight <= 50:
        size_options.append("M")
    if length <= 33 and width <= 20 and height <= 30 and weight <= 100:
        size_options.append("L")
    if not size_options:
        raise HTTPException(status_code=400, detail="Parcel dimensions exceed all available sizes")
    return size_options


    
def get_user_id_by_recipient_info(db: Session, email: str, phone: str, name: str) -> int:
    # Query the user by email
    user = db.query(Account).filter(Account.email == email).first()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Recipient not found")
    return user.user_id

#filter by shipper_id to get the completed order
@router.get("/shippers/{shipper_id}/completed-orders", response_model=List[CompletedOrderResponse])
def get_completed_orders_by_shipper(shipper_id: int, db: Session = Depends(get_db)):
    # Check if the shipper exists and has role = 3
    shipper = db.query(Shipper).join(Account).filter(Shipper.shipper_id == shipper_id, Account.role == 3).first()
    
    if not shipper:
        raise HTTPException(status_code=404, detail="Shipper with given ID not found or does not have the role of a shipper")

    # Query for orders completed by this shipper
    completed_orders = db.query(Order).filter(
        Order.order_id == shipper.order_id,
        Order.order_status == 'Completed'
    ).all()

    if not completed_orders:
        raise HTTPException(status_code=404, detail="No completed orders found for this shipper")

    return [
        CompletedOrderResponse(
            order_id=order.order_id,
            recipient_id=order.recipient_id,
            sending_date=order.sending_date,
            receiving_date=order.receiving_date,
            order_status=order.order_status
        ) for order in completed_orders
    ]


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

#get order by paging
@router.get("/",response_model=Dict[str, Any])
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
            sending_locker= sending_locker.locker_id,
            receiving_locker= receiving_locker.locker_id,
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

#GET order bằng parcel_id
@router.get("/{order_id}", response_model=OrderResponse)
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
    response = OrderResponse(
        order_id=order.order_id,
        sender_id=order.sender_id,
        sender_informations=sender_info,
        recipient_id=order.recipient_id,
        sending_locker= sending_locker.locker_id,
        receiving_locker= receiving_locker.locker_id,
        ordering_date=order.ordering_date,
        sending_date=order.sending_date,
        receiving_date=order.receiving_date,
        order_status=order.order_status,
        parcel = parcel_info
    )
    
    return response
#update order by user_id    
@router.put("/{parcel_id}", response_model=OrderRequest)
def update_package(parcel_id: int, _package: OrderRequest, db: Session = Depends(get_db)):
    # Allow for partial updates
    package_put = db.query(Order).filter(Order.order_id == parcel_id).update(
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


#delete order bằng parcel_id
@router.delete("/{order_id}")
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
    db.delete(order_delete)
    db.commit()
    
    return {
        "Message": "Order and parcel deleted"
    }

# Get cell
@router.get("/{locker_id}/{parcel_id}", response_model=OrderRequest)
def get_cell(locker_id: str, parcel_id: int, db: Session = Depends(get_db)):
    package = db.query(Order).filter(Order.locker_id == locker_id).filter(Order.parcel_id == parcel_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Order not found")
    return package




#Update receving_date and sending_date
@router.put("/receving_date")
def update_package(order_id : int , recive_date: date, db: Session = Depends(get_db)):

    order = db.query(Order).filter(Order.order_id == order_id).first()
    # Check if order exists
    # If not, raise an error
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.receiving_date = recive_date
    db.commit()
    db.refresh(order)  # Refresh to get the updated order details
    return {
        "Message": "Receiving date updated",
        "order_id": order_id,
        "receiving_date": order.receiving_date
    }
    
@router.put("/sending_date")
def update_package(order_id : int , send_date: date, db: Session = Depends(get_db)):

    order = db.query(Order).filter(Order.order_id == order_id).first()
    # Check if order exists
    # If not, raise an error
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.sending_date = send_date
    db.commit()
    db.refresh(order)  # Refresh to get the updated order details
    return {
        "Message": "Sending date updated",
        "order_id": order_id,
        "sending_date": order.sending_date
    }
    


@router.put("/order/{order_id}/status")
def update_order_status(order_id: int, status_request: UpdateOrderStatusRequest, db: Session = Depends(get_db)):
    # Find the order in the database
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Update the order status
    order.order_status = status_request.status

    # Commit the changes to the database
    db.commit()
    db.refresh(order)
    
    return {
        "Message": "Status updated",
        "order_id": order_id,
        "current status:": status_request.status
    }