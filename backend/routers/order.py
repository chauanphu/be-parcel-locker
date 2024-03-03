from datetime import date
from fastapi import APIRouter, status, Response, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
from random import randrange
from routers.user import my_posts
router = APIRouter(
    prefix="/order",
    tags=["order"],
)
class OrderRequest(BaseModel):
    #package_id: str
    sender_id: int
    recipient_id: str
    sending_locker_id: str
    receiving_locker_id: str
    ordering_date:date
    sending_date: date
    receiving_date: date

my_order = [{"package":111, "sender":123, "recipient":"recipient 1","sending_locker":"sending_locker 1",
              "receiving_locker":"receiving_locker 1", "sending_date":"sending_date 1", "receiving_date":"receiving_date 1"}   ]

#tạo một package_id bằng random (khi tạo bằng sequence thì bị lỗi nên mình để tạm randrange)
@router.post("/createorder", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderRequest):
    order_dict = order.dict()
    order_dict['package_id'] = randrange(1,999999)
    my_order.append(order_dict)
    return {'data':order_dict}

#hàm để tìm gói hàng
def find_package_id(package_id):
    for d in my_order:
        if d["package_id"] == package_id:
            return d

#GET order bằng package_id
@router.get("/find_package_id/{package_id}")
def get_package_id(package_id: int, response : Response):

    find = find_package_id(package_id)
    
    if not find:

        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,
                             detail = f"find with package_id:{package_id} was not found")
    return {"find_detail": find}

#hàm để tìm xem user_id có trùng với sender_id không
#nếu có thì có order 
def find_sth(user_id):
    for order in my_order:
        sender_id = order["sender_id"]
        for post in my_posts:
            if order["sender_id"] == user_id:
                return order
    return None


#GET order bằng cả user và package
@router.get("/find_id_ne/{user_id}/{package_id}")
def get_package_by_id (user_id: int,package_id:int, response: Response):
    find_theid = find_sth(user_id)
    if not find_theid:

        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,
                             detail = f"find with user_id:{user_id} and package_id:{package_id} was not found")
    return {"find_detail": find_theid}


#Hàm cho put và delete
def find_index_order(package_id):
    for j,k in enumerate(my_order):
        if k['package_id'] == package_id:
            return j

#update order bằng package_id    
@router.put("/put_order/{package_id}")
def update_order(package_id: int, order: OrderRequest):

    order_index = find_index_order(package_id)

    if order_index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = f"post with package_id:{package_id} does not exits")
    order_dict = order.dict()
    order_dict['package_id'] = package_id
    my_order[order_index] = order_dict
    return {'data': order_dict}


#delete order bằng package_id
@router.delete("/delete_order/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(package_id:int):
    order_index = find_index_order(package_id)

    if order_index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = f"post with package_id:{package_id} does not exits")

    my_order.pop(order_index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

