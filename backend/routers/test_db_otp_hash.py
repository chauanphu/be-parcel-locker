
from fastapi import APIRouter, HTTPException,Depends
from auth.utils import get_current_user
# This is hash table set up
class Node:
    def __init__(self, order_id, otp):
        self.order_id = order_id
        self.otp = otp
        self.next = None

class HashTable:
    def __init__(self, size=100):
        self.size = size
        self.table = [None] * size

    def _hash(self, key):
        return key % self.size

    def insert(self, order_id, otp):
        index = self._hash(order_id)
        new_node = Node(order_id, otp)
        if self.table[index] is None:
            self.table[index] = new_node
        else:
            current = self.table[index]
            while current.next is not None:
                if current.order_id == order_id:
                    current.otp = otp  # Update OTP if order_id already exists
                    return
                current = current.next
            if current.order_id == order_id:
                current.otp = otp  # Update OTP if order_id already exists
            else:
                current.next = new_node

    def find(self, order_id):
        index = self._hash(order_id)
        current = self.table[index]
        while current is not None:
            if current.order_id == order_id:
                return current.otp
            current = current.next
        return None

    def delete(self, order_id):
        index = self._hash(order_id)
        current = self.table[index]
        previous = None
        while current is not None:
            if current.order_id == order_id:
                if previous is None:
                    self.table[index] = current.next
                else:
                    previous.next = current.next
                return True
            previous = current
            current = current.next
        return False

    def display(self):
        for i, node in enumerate(self.table):
            current = node
            if current:
                print(f"Index {i}: ", end="")
                while current:
                    print(f"Order ID: {current.order_id}, OTP: {current.otp}", end=" -> ")
                    current = current.next
                print("None")


hash_table = HashTable()
router = APIRouter( 
    prefix="/OTP_hashtable",
    tags=["OTP_hashtable"],
    dependencies=[Depends(get_current_user)]
)
@router.post("/store/")
def store_order(order_id: int, otp: str):
    hash_table.insert(order_id, otp)
    return {"message": "Data stored successfully"}

@router.get("/retrieve/{order_id}")
def retrieve_order(order_id: int):
    otp = hash_table.find(order_id)
    if otp is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order_id, "otp": otp}

@router.delete("/delete/{order_id}")
def delete_order(order_id: int):
    deleted_node = hash_table.delete(order_id)
    if deleted_node is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Data deleted successfully"}
