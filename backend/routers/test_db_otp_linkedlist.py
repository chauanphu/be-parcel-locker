
from fastapi import APIRouter, HTTPException,Depends
from auth.utils import get_current_user
# This is linked list set up
class Node:
    def __init__(self, order_id, otp):
        self.order_id = order_id
        self.otp = otp
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def insert(self, order_id, otp):
        new_node = Node(order_id, otp)
        new_node.next = self.head
        self.head = new_node

    def find(self, order_id):
        current = self.head
        while current is not None:
            if current.order_id == order_id:
                return current.otp
            current = current.next
        return None

    def delete(self, order_id):
        current = self.head
        previous = None
        while current is not None and current.order_id != order_id:
            previous = current
            current = current.next
        if current is None:
            return None
        if previous is None:
            self.head = current.next
        else:
            previous.next = current.next
        return current

    def display(self):
        current = self.head
        while current is not None:
            print(f"Order ID: {current.order_id}, OTP: {current.otp}")
            current = current.next


linked_list = LinkedList()
router = APIRouter( 
    prefix="/OTP_LINKEDLIST",
    tags=["OTP_LINKEDLIST"],
    dependencies=[Depends(get_current_user)]
)
@router.post("/store/")
def store_order(order_id: int, otp: str):
    linked_list.insert(order_id, otp)
    return {"message": "Data stored successfully"}

@router.get("/retrieve/{order_id}")
def retrieve_order(order_id: int):
    otp = linked_list.find(order_id)
    if otp is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order_id, "otp": otp}

@router.delete("/delete/{order_id}")
def delete_order(order_id: int):
    deleted_node = linked_list.delete(order_id)
    if deleted_node is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Data deleted successfully"}
