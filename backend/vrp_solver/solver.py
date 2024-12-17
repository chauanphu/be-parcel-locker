from typing import Dict, List
from .load_data import get_cache_orders
from states.shipment import Route, Location, Order as VRPOrder, set_route
from utils.redis import redis_client


def _merge_orders(orders: List[VRPOrder]) -> List[VRPOrder]:
    """
    Merge the orders with the same sending and receiving locker
    """
    # Group the orders by sending and receiving locker
    order_group: Dict[str, Dict] = {}
    for order in orders:
        sending_locker_id = redis_client.hget(f"order:{order.order_id}", "sending_locker_id")
        receiving_locker_id = redis_client.hget(f"order:{order.order_id}", "receiving_locker_id")
        key = f"{sending_locker_id}-{receiving_locker_id}"
        if key not in order_group:
            order_group[key] = {}
            order_group[key]['orders'] = []
            order_group[key]['sending_locker'] = {
                "id": receiving_locker_id,
                "latitude": redis_client.hget(f"order:{order.order_id}", "sending_latitude"),
                "longitude": redis_client.hget(f"order:{order.order_id}", "sending_longitude")
            }
            order_group[key]['receiving_locker'] = {
                "id": receiving_locker_id,
                "latitude": redis_client.hget(f"order:{order.order_id}", "receiving_latitude"),
                "longitude": redis_client.hget(f"order:{order.order_id}", "receiving_longitude")
            }
        order_group[key]['orders'].append(order)

    for idx, (key, order_list) in enumerate(order_group.items()):
        route = Route(idx)
        sending_location = Location(
            locker_id=order_list['sending_locker']['id'],
            latitude=order_list['sending_locker']['latitude'],
            longitude=order_list['sending_locker']['longitude'],
            pickup_orders=order_list['orders']
        )
        receiving_location = Location(
            locker_id=order_list['receiving_locker']['id'],
            latitude=order_list['receiving_locker']['latitude'],
            longitude=order_list['receiving_locker']['longitude'],
            dropoff_orders=order_list['orders']
        )
        route.add_location(sending_location)
        route.add_location(receiving_location)
        set_route(route)

def solve_vrp():
    orders: List[VRPOrder] = get_cache_orders()
    _merge_orders(orders)
    