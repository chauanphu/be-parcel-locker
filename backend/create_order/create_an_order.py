from pydantic import BaseModel
from fastapi import FastAPI, status
from datetime import date

create_an_order = FastAPI()
class Order(BaseModel):
    package: str
    sender: str
    recipient: str
    sending_locker: str
    receiving_locker: str
    sending_date: date
    receiving_date: date

my_order = [{"package":"package 1", "sender":"sender 1", "recipient":"recipient 1","sending_locker":"sending_locker 1",
              "receiving_locker":"receiving_locker 1", "sending_date":"sending_date 1", "receiving_date":"receiving_date 1"}   ]


@create_an_order.post("/createorder", status_code=status.HTTP_201_CREATED)
def create_order(order: Order):
	order_dict = order.dict()
	my_order.append(order_dict)
	return{"data":order_dict}
