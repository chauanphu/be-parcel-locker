from typing import List
from models.order import OrderStatus
from utils.redis import redis_client
import json
from database import SessionLocal
from models.order import Order as OrderModel
import logging

class Order:
    """
    This model represents the order of the customer
    """
    def __init__(self, order_id: int, size: float, weight: float):
        self.order_id = order_id
        self.size = size
        self.weight = weight
        self.__dict__ = {
            "order_id": self.order_id,
            "size": self.size,
            "weight": self.weight
        }
    def to_dict(self):
        return self.__dict__

class Location:
    """
    This model represents the location of the customer
    """
    def __init__(self, locker_id: int, latitude: float, longitude: float, pickup_orders: List[Order] = [], dropoff_orders: List[Order] = []):
        self.locker_id = locker_id
        self.latitude = latitude
        self.longitude = longitude
        self.pickup_orders = pickup_orders
        self.dropoff_orders = dropoff_orders

    def to_dict(self):
        return {
            "locker_id": self.locker_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "pickup_orders": [order.to_dict() for order in self.pickup_orders],
            "dropoff_orders": [order.to_dict() for order in self.dropoff_orders]
        }

class Route:
    """
    This model represents the shipping route of shipper, which contains the visited location and the pickup/dropoff orders
    """
    def __init__(self, route_id) -> None:
        self.route_id = route_id
        self.visit_locations: List[Location] = []
        self.__dict__.update({
            "locations": [location.to_dict() for location in self.visit_locations]
        })

    def to_dict(self):
        return {
            "route_id": self.route_id,
            "locations": [location.to_dict() for location in self.visit_locations]
        }
    
    def add_location(self, location: Location):
        self.visit_locations.append(location)
        self.__dict__.update({
            "locations": [location.to_dict() for location in self.visit_locations]
        })

    def is_empty(self):
        return not bool(self.visit_locations)
    
    @classmethod
    def parse_from_dict(cls, data: dict):
        route = cls(data['route_id'])
        for location in data['locations']:
            route.visit_locations.append(Location(location['locker_id'], location['latitude'], location['longitude'], 
            [Order(order['order_id'], order['size'], order['weight']) for order in location['pickup_orders']],
            [Order(order['order_id'], order['size'], order['weight']) for order in location['dropoff_orders']]))
        return route

def set_route(route: Route):
    """
    This function sets the route of the shipper to Redis
    """
    if route.is_empty():
        return
    updated_route = json.dumps(route.to_dict())
    redis_client.set(f'route:{route.route_id}', updated_route)

def get_route(route_id: int) -> Route:
    """
    This function gets the route of the shipper from Redis
    """
    result = redis_client.get(f'route:{route_id}')
    if result:
        result = json.loads(result)
        return result
    return None

def deque_route() -> Route:
    """
    This function dequeues the route from Redis
    """
    try:
        keys = redis_client.keys('route:*')
        if keys:
            keys.sort(key=lambda x: int(x.split(':')[1]))  # Sort keys based on the route number
            route_id = keys.pop(0).split(':')[1]  # Get the first route id
            route = redis_client.get(f'route:{route_id}')
            logging.debug(f"Route from Redis: {route}")
            
            if not route:
                logging.error("Route is None or empty")
                return None
                
            try:
                result = json.loads(route)
                return result
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}, Route: {route}")
                return None
    except Exception as e:
        logging.error(f"Error in deque_route: {str(e)}")
        return None
    return None

def assign_orders_to_shipper(shipper_id: int, route: dict):
    """
    This function assigns the route to the shipper
    """
    # Get all the orders from the route
    order_ids: set = set()
    for location in route['locations']:
        order_ids.update([order['order_id'] for order in location.get('pickup_orders', [])])
        order_ids.update([order['order_id'] for order in location.get('dropoff_orders', [])])

    # Set the orders to Redis
    for id in order_ids:
        redis_client.hset(f'order:{id}', 'shipper_id', shipper_id)
        redis_client.sadd(f"tracking:{shipper_id}", id)
        
    # Update the shipper id into each order in the postgres database
    with SessionLocal() as db:
        for id in order_ids:
            order: OrderModel = db.query(OrderModel).filter(OrderModel.order_id == id).first()
            if order:
                order.shipper_id = shipper_id
                db.add(order)
        db.commit()

    # Copy route:route_id to shipper_route:shipper_id
    redis_client.set(f'shipper:{shipper_id}', json.dumps(route))
    redis_client.delete(f'route:{route["route_id"]}')

def track_order(order_id: int) -> tuple[float, float]:
    """
    This function tracks the order from Redis
    """
    shipper_id = redis_client.hget(f'order:{order_id}', 'shipper_id')
    status = redis_client.hget(f'order:{order_id}', 'status')
    if shipper_id and status == OrderStatus.Ongoing.value:
        result = redis_client.hgetall(f'shipper_location:{shipper_id}')
        return result['latitude'], result['longitude']
    return None

def get_orders_by_shipper(shipper_id: int):
    """
    This function gets the orders assigned to the shipper from Redis
    """
    order_ids = redis_client.smembers(f"tracking:{shipper_id}")
    return redis_client.smembers(f"tracking:{shipper_id}")

def update_location(shipper_id: int, latitude: float, longitude: float):
    # Get all the orders assigned to the shipper
    redis_client.hmset(f'shipper_location:{shipper_id}', {'latitude': latitude, 'longitude': longitude})

def finish_route(shipper_id: int):
    redis_client.delete(f'shipper:{shipper_id}')
    redis_client.delete(f"shipper_location:{shipper_id}")
    redis_client.delete(f"tracking:{shipper_id}")

def drop_order(order_id: int) -> bool:
    # Check if the order is in the shipper
    order = redis_client.hgetall(f'order:{order_id}')
    if order:
        order['status'] = OrderStatus.Delivered.value
        redis_client.hmset(f'order:{order_id}', order)
    return True

def pickup_order(order_id: int) -> bool:
    order = redis_client.hgetall(f'order:{order_id}')
    if order:
        order['status'] = OrderStatus.Ongoing.value
        redis_client.hmset(f'order:{order_id}', order)
    return True