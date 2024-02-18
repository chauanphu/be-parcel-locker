from datetime import date
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()

class CreateOrder(BaseModel):
    package: str
    sender: str
    recipient: str
    sending_locker: str
    receiving_locker: str
    sending_date: date
    receiving_date: date

my_order = [{"package":"package 1", "sender":"sender 1", "recipient":"recipient 1","sending_locker":"sending_locker 1",
              "receiving_locker":"receiving_locker 1", "sending_date":"sending_date 1", "receiving_date":"receiving_date 1"}   ]


@router.post("/createorder", status_code=status.HTTP_201_CREATED)
def create_order(order: CreateOrder):
	order_dict = order.dict()
	my_order.append(order_dict)
	return{"data":order_dict}

