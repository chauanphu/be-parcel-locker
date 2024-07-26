from datetime import date
import uuid
from fastapi import APIRouter, Depends
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.utils import get_current_user
from sqlalchemy.orm import Session, joinedload, aliased
from database.session import get_db
from models.locker import Cell, Locker
from models.order import Order
from routers.locker import LockerInfoResponse
from routers.parcel import ParcelRequest, Parcel
from enum import Enum

router = APIRouter(
    prefix="/order",
    tags=["order"],
    dependencies=[Depends(get_current_user)]
)

class OrderStatusEnum(str, Enum):
    Ongoing = 'Ongoing'
    Canceled = 'Canceled'
    Completed = 'Completed'

class ParcelResponse(BaseModel):
    width: int
    length: int
    height: int
    weight: int
    parcel_size: str

class ParcelRequest(BaseModel):
    width: int
    length: int
    height: int
    weight: int
    # parcel_size: str

class OrderRequest(BaseModel):
    parcel: ParcelRequest
    sender_id: int
    recipient_id: int
    sending_locker_id: int
    receiving_locker_id: int
    ordering_date:date
    sending_date: date
    receiving_date: date
    

class OrderResponse(BaseModel):
    order_id: int
    parcel: ParcelResponse
    sender_id: int
    recipient_id: int
    sending_locker: LockerInfoResponse
    receiving_locker: LockerInfoResponse
    ordering_date:date
    sending_date: date
    receiving_date: date
    parcel: ParcelRequest
    # status: OrderStatusEnum
class Token2(BaseModel):
    order_id: int
    message: str
    parcel_size: str

    
# Return all order along with their parcel and locker
def join_order_parcel_cell(db: Session = Depends(get_db)):
    query = db.query(Order).options(joinedload(Order.parcel)).join(Parcel, Order.order_id == Parcel.parcel_id)
    return query

def find_available_cell(locker_id: int, db: Session = Depends(get_db)):
    """
    Finds an available cell in the specified locker.

    Parameters:
    - locker_id (int): The ID of the locker to search for available cells.
    - db (Session): The database session to use for the query.

    Returns:
    - Cell: The first available cell found in the locker, or None if no available cells are found.
    """
    query = db.query(Cell).filter(Cell.locker_id == locker_id).filter(Cell.occupied == False)
    return query.first()

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

def determine_parcel_size(width: int, length: int, height: int, weight: int) -> str:
    # Define thresholds for parcel sizes based on individual dimensions and weight
    if width <= 10 and length <= 10 and height <= 10 and weight <= 100:
        return "S"
    elif width <= 20 and length <= 20 and height <= 20 and weight <= 100:
        return "M"
    elif width <= 30 and length <= 30 and height <= 30 and weight <= 100:
        return "L"
    else:
        raise HTTPException(status_code=400, detail="Over size or weight limit (quá cỡ hoặc quá trọng lượng)")

#tạo order
@router.post("/", response_model=Token2)
def create_order(order: OrderRequest, db: Session = Depends(get_db)):
    new_order = order.dict(exclude_none=True, exclude_unset=True)
    parcel = new_order.pop('parcel')
    sending_locker_id = new_order.pop('sending_locker_id')
    receiving_locker_id = new_order.pop('receiving_locker_id')

    sending_cell = find_available_cell(sending_locker_id, db)
    receiving_cell = find_available_cell(receiving_locker_id, db)

    if not sending_cell or not receiving_cell:
        raise HTTPException(status_code=400, detail="No available cells in the locker")

    change_cell_occupied(sending_cell.cell_id, True, db)
    change_cell_occupied(receiving_cell.cell_id, True, db)

    new_order['sending_cell_id'] = sending_cell.cell_id
    new_order['receiving_cell_id'] = receiving_cell.cell_id
    new_order_instance = Order(**new_order)
    db.add(new_order_instance)
    db.commit()
    db.refresh(new_order_instance)

    parcel['parcel_id'] = new_order_instance.order_id
    parcel_size = determine_parcel_size(parcel['width'], parcel['length'], parcel['height'], parcel['weight'])
    parcel['parcel_size'] = parcel_size
    new_parcel = Parcel(**parcel)
    db.add(new_parcel)
    db.commit()

    return {
        "order_id": new_order_instance.order_id,
        "message": 'Successfully created',
        "parcel_size": parcel_size
    }


#GET order bằng parcel_id
@router.get("/{order_id}", response_model=OrderResponse)
def get_package(order_id: int, db: Session = Depends(get_db), ):
    query = join_order_parcel_cell(db)
    query = query.filter(Order.order_id == order_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Order not found")
    # Convert the order: Order to a dict and remove the sending_cell_id and receiving_cell_id
    order = to_dict(query)
    sending_cell_id = order.pop('sending_cell_id', None)
    receiving_cell_id = order.pop('receiving_cell_id', None)
    # Add the sending and receiving locker to the order
    sending_locker = find_locker_by_cell(sending_cell_id, db)
    receiving_locker = find_locker_by_cell(receiving_cell_id, db)
    order['sending_locker'] = to_dict(sending_locker)
    order['receiving_locker'] = to_dict(receiving_locker)
    order['parcel'] = to_dict(order['parcel'])
    return order

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
@router.delete("/{parcel_id}", response_model=str)
def delete_package(parcel_id: int, db: Session = Depends(get_db)):
    package_delete = db.query(Order).filter(Order.order_id == parcel_id).first()
    #nếu order không được tìm thấy thì là not found
    if not package_delete:
        raise HTTPException(status_code=404, detail="Order not found")
    #nếu xóa rồi mà quên xong xóa thêm lần nữa thì hiện ra là k tồn tại
    if package_delete == None:
        raise HTTPException(status_code=404, detail="Order not exist")

    db.delete(package_delete)
    db.commit()
    return {
        "Message": "Order deleted"
    }

# Get cell
@router.get("/{locker_id}/{parcel_id}", response_model=OrderRequest)
def get_cell(locker_id: str, parcel_id: int, db: Session = Depends(get_db)):
    package = db.query(Order).filter(Order.locker_id == locker_id).filter(Order.parcel_id == parcel_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Order not found")
    return package