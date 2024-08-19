from fastapi import APIRouter, HTTPException, Depends
from auth.utils import get_current_user

class TreeNode:
    def __init__(self, order_id, otp):
        self.order_id = order_id
        self.otp = otp
        self.left = None
        self.right = None

class BinarySearchTree:
    def __init__(self):
        self.root = None

    def insert(self, order_id, otp):
        if self.root is None:
            self.root = TreeNode(order_id, otp)
        else:
            self._insert(self.root, order_id, otp)

    def _insert(self, node, order_id, otp):
        if order_id < node.order_id:
            if node.left is None:
                node.left = TreeNode(order_id, otp)
            else:
                self._insert(node.left, order_id, otp)
        elif order_id > node.order_id:
            if node.right is None:
                node.right = TreeNode(order_id, otp)
            else:
                self._insert(node.right, order_id, otp)
        else:
            node.otp = otp  # Update OTP if order_id already exists

    def find(self, order_id):
        return self._find(self.root, order_id)

    def _find(self, node, order_id):
        if node is None:
            return None
        elif order_id < node.order_id:
            return self._find(node.left, order_id)
        elif order_id > node.order_id:
            return self._find(node.right, order_id)
        else:
            return node.otp

    def delete(self, order_id):
        self.root, deleted = self._delete(self.root, order_id)
        return deleted

    def _delete(self, node, order_id):
        if node is None:
            return node, None

        if order_id < node.order_id:
            node.left, deleted = self._delete(node.left, order_id)
        elif order_id > node.order_id:
            node.right, deleted = self._delete(node.right, order_id)
        else:
            if node.left is None:
                return node.right, node
            elif node.right is None:
                return node.left, node

            min_larger_node = self._get_min(node.right)
            node.order_id, node.otp = min_larger_node.order_id, min_larger_node.otp
            node.right, _ = self._delete(node.right, min_larger_node.order_id)
            deleted = node

        return node, deleted

    def _get_min(self, node):
        while node.left is not None:
            node = node.left
        return node

# Create an instance of BinarySearchTree
bst = BinarySearchTree()

# FastAPI router and endpoints
router = APIRouter(
    prefix="/OTP_tree",
    tags=["OTP_tree"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/store/")
def store_order(order_id: int, otp: str):
    bst.insert(order_id, otp)
    return {"message": "Data stored successfully"}

@router.get("/retrieve/{order_id}")
def retrieve_order(order_id: int):
    otp = bst.find(order_id)
    if otp is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order_id, "otp": otp}

@router.delete("/delete/{order_id}")
def delete_order(order_id: int):
    deleted_node = bst.delete(order_id)
    if deleted_node is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Data deleted successfully"}
