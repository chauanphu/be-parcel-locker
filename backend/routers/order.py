from datetime import date
from fastapi import APIRouter, Depends, status
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.utils import get_current_user
from sqlalchemy.orm import Session
from database.session import get_db
from models.order import Order
from routers.parcel import ParcelRequest
from typing import List

router = APIRouter(
    prefix="/order",
    tags=["order"],
    dependencies=[Depends(get_current_user)]
)
class OrderRequest(BaseModel):
    sender_id: str
    recipient_id: str
    sending_locker_id: str
    receiving_locker_id: str
    ordering_date: date
    sending_date: date
    receiving_date: date

class OrderResponse(OrderRequest):
    order_id: int
    sender_id: str
    recipient_id: str
    sending_locker_id: str
    receiving_locker_id: str
    ordering_date:date
    sending_date: date
    receiving_date: date
    parcels: ParcelRequest


#create order that can add as many parcel as user needs
@router.post("/", response_model=OrderRequest)
def create_order(order: OrderRequest, db: Session = Depends(get_db)):
    new_order = Order(**order.model_dump())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

#Get all orders and parcels that has the order_id of that order of a defined sender_id
@router.get("/{sender_id}", response_model=List[OrderResponse])
def get_order(sender_id: str, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.sender_id == sender_id).all()
    if not orders:
        raise HTTPException(status_code=404, detail="User has not created any orders")
    return orders


#update order by user_id    
@router.put("/{parcel_id}", response_model=OrderRequest)
def update_package(parcel_id: int, _package: OrderRequest, db: Session = Depends(get_db)):
    # Allow for partial updates
    package_put = db.query(Order).filter(Order.parcel_id == parcel_id).update(
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
    package_delete = db.query(Order).filter(Order.parcel_id == parcel_id).first()
    #nếu order không được tìm thấy thì là not found
    if not package_delete:
        raise HTTPException(status_code=404, detail="Order not found")
    #nếu xóa rồi mà quên xong xóa thêm lần nữa thì hiện ra là k tồn tại
    if package_delete == None:
        raise HTTPException(status_code=404, detail="Order not exist")

    db.delete(package_delete)
    db.commit()
    return package_delete

# Get cell
@router.get("/{locker_id}/{parcel_id}", response_model=OrderRequest)
def get_cell(locker_id: str, parcel_id: int, db: Session = Depends(get_db)):
    package = db.query(Order).filter(Order.locker_id == locker_id).filter(Order.parcel_id == parcel_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Order not found")
    return package