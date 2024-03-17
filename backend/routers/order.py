from datetime import date
from fastapi import APIRouter, Depends
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.utils import get_current_user
from sqlalchemy.orm import Session, joinedload
from database.session import get_db
from models.order import Order
from models.parcel import Parcel
from typing import List

router = APIRouter(
    prefix="/order",
    tags=["order"],
    dependencies=[Depends(get_current_user)]
)

class ParcelRequest(BaseModel):
    width: int
    length: int
    height: int
    weight: int
    parcel_size: str

class OrderRequest(BaseModel):
    parcel: ParcelRequest
    sender_id: int
    recipient_id: int
    sending_locker_id: str
    receiving_locker_id: str
    ordering_date:date
    sending_date: date
    receiving_date: date

class OrderResponse(BaseModel):
    order_id: int
    parcel: ParcelRequest
    sender_id: int
    recipient_id: int
    sending_locker_id: str
    receiving_locker_id: str
    ordering_date:date
    sending_date: date
    receiving_date: date

# Return all order along with their parcels
def join_order_parcel(db: Session = Depends(get_db)):
    query = db.query(Order).options(joinedload(Order.parcel)).join(Parcel, Order.order_id == Parcel.parcel_id)
    return query.all()

#tạo order
@router.post("/")
def create_order(order: OrderRequest, db: Session = Depends(get_db)):
    new_order = order.model_dump(exclude_none=True, exclude_unset=True)
    parcel = new_order.pop('parcel')
    new_order = Order(**new_order)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    parcel['parcel_id'] = new_order.order_id
    new_parcel = Parcel(**parcel)
    db.add(new_parcel)
    db.commit()
    # Return the newly created order with the parcel for OrderResponse
    query = db.query(Order).join(Parcel, Order.order_id == Parcel.parcel_id)
    return query.filter(Order.order_id == new_order.order_id).first()


#GET order bằng parcel_id
@router.get("/{parcel_id}")
def get_package(parcel_id: int, db: Session = Depends(get_db), ):
    query = join_order_parcel(db)
    if not query:
        raise HTTPException(status_code=404, detail="Order not found")
    return query
    

#GET order bằng cả user và package
@router.get("/{user_id}/{parcel_id}", response_model=OrderRequest)
def get_package(user_id: int, parcel_id: int, db: Session = Depends(get_db)):
    package = db.query(Order).filter(Order.user_id == user_id, Order.order_id == parcel_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Order not found")
    return package


#update order bằng parcel_id    
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
@router.delete("/{parcel_id}", response_model=OrderRequest)
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
    return package_delete

