from datetime import date
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.session import get_db
from models.order import Order

router = APIRouter(
    prefix="/order",
    tags=["order"],
)
class OrderRequest(BaseModel):
    package_id: int
    sender_id: int
    recipient_id: int
    sending_locker_id: str
    receiving_locker_id: str
    ordering_date:date
    sending_date: date
    receiving_date: date


#tạo order
@router.post("/", response_model=OrderRequest)
def create_order(order: OrderRequest, db: Session = Depends(get_db)):
#Đối tượng new_order mới được tạo sẽ được thêm vào database bằng phương thức add()
    new_order = Order(**order.dict())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


#GET order bằng package_id
@router.get("/{package_id}", response_model= OrderRequest)
def get_package(package_id: int, db: Session = Depends(get_db), ):
    package = db.query(Order).filter(Order.package_id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Order not found")
    return package
    

#GET order bằng cả user và package
@router.get("/{user_id}/{package_id}", response_model=OrderRequest)
def get_package(user_id: int, package_id: int, db: Session = Depends(get_db)):
    package = db.query(Order).filter(Order.user_id == user_id, Order.package_id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Order not found")
    return package


#update order bằng package_id    
@router.put("/{package_id}", response_model=OrderRequest)
def update_package(package_id: int, _package: OrderRequest, db: Session = Depends(get_db)):
    # Allow for partial updates
    package_put = db.query(Order).filter(Order.package_id == package_id).update(
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


#delete order bằng package_id
@router.delete("/{package_id}", response_model=OrderRequest)
def delete_package(package_id: int, db: Session = Depends(get_db)):
    package_delete = db.query(Order).filter(Order.package_id == package_id).first()
    #nếu order không được tìm thấy thì là not found
    if not package_delete:
        raise HTTPException(status_code=404, detail="Order not found")
    #nếu xóa rồi mà quên xong xóa thêm lần nữa thì hiện ra là k tồn tại
    if package_delete == None:
        raise HTTPException(status_code=404, detail="Order not exist")

    db.delete(package_delete)
    db.commit()
    return package_delete

