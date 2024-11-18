from typing import List
from .load_data import get_cache_orders
from models.locker import Locker
from states.shipment import Route, Location, Order as VRPOrder, set_route
from utils.redis import redis_client
from database import SessionLocal

def solve_vrp():
    orders: List[VRPOrder] = get_cache_orders()
    # Solve the VRP, based on naive approach
    # Assuming each order has a different route
    with SessionLocal() as db:
        for index, order in enumerate(orders):
            order_cache = redis_client.hgetall(f"order:{order.order_id}")
            route = Route(index)
            # Get the locker location from the database
            sending_locker = db.query(Locker).filter(Locker.locker_id == order_cache.get("sending_locker_id")).first()
            receiving_locker = db.query(Locker).filter(Locker.locker_id == order_cache.get("receiving_locker_id")).first()
            sending_location = Location(
                locker_id=sending_locker.locker_id,
                latitude=sending_locker.latitude,
                longitude=sending_locker.longitude,
                pickup_orders=[order]
            )
            receiving_location = Location(
                locker_id=receiving_locker.locker_id,
                latitude=receiving_locker.latitude,
                longitude=receiving_locker.longitude,
                dropoff_orders=[order]
            )
            route.add_location(sending_location)
            route.add_location(receiving_location)
            set_route(route)