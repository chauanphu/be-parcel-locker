
from typing import List
from states.shipment import Route, Location, Order as VRPOrder, set_route
from utils.redis import redis_client

# Get all order with status Ongoing and create a route for them.
# The redis store all order cache in a hash with key "order:{order_id}".
# hash field: sending_locker_id, receiving_locker_id, status, weight, size
def get_cache_orders() -> List[VRPOrder]:
    orders = []
    for key in redis_client.scan_iter("order:*"):
        order = redis_client.hgetall(key)
        if order["status"] != "Waiting":
            continue
        order_id = key.split(":")[1]
        orders.append(VRPOrder(
            order_id,
            order.get("weight"),
            order.get("size")
        ))
    return orders
