from datetime import date
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(
    prefix="/order",
    tags=["order"],
)
class OrderRequest(BaseModel):
    package_id: str
    sender_id: str
    recipient_id: str
    sending_locker_id: str
    receiving_locker_id: str
    ordering_date:date
    sending_date: date
    receiving_date: date

my_order = [{"package":"package 1", "sender":"sender 1", "recipient":"recipient 1","sending_locker":"sending_locker 1",
              "receiving_locker":"receiving_locker 1", "sending_date":"sending_date 1", "receiving_date":"receiving_date 1"}   ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderRequest):
	order_dict = order.dict()
	my_order.append(order_dict)
	return{"data":order_dict}

@router.get("/", status_code=status.HTTP_200_OK, response_model=list[OrderRequest])
def get_all_orders():
    return my_order
#this returns a list of all orders stored in the my_order list.

@router.get("/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderRequest)
def get_order_by_id(order_id: int):
    for order in my_order:
        if order["id"] == order_id:
            return order
    return {"error": "Order not found"}