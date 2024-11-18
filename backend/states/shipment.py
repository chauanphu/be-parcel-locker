from typing import List
from models.order import OrderStatus
from utils.redis import redis_client
import json

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

# def assign_orders_to_shipper(shipper_id: int, route: dict):
#     """
#     This function assigns the route to the shipper
#     """
#     # Get all the orders from the route
#     order_ids: set[int] = set()
#     # Parse the route to Route object
#     route: Route = Route.parse_from_dict(route)
#     for location in route.visit_locations:
#         order_ids.update([order.order_id for order in location.pickup_orders])
#         order_ids.update([order.order_id for order in location.dropoff_orders])

#     # Set the orders to Redis
#     for id in order_ids:
#         redis_client.hset(f'order:{id}', 'shipper_id', shipper_id)
#     # Add all order_ids to the the shipper using add member function of Redis
#     redis_client.sadd(f'shipper:{shipper_id}', *order_ids)

def update_location(shipper_id: int, latitude: float, longitude: float):
    # Get all the orders assigned to the shipper
    orders = redis_client.smembers(f'shipper:{shipper_id}')
    for order_id in orders:
        order = redis_client.hgetall(f'order:{order_id}')
        if order:
            order['latitude'] = latitude
            order['longitude'] = longitude
            redis_client.hmset(f'order:{order_id}', order)

def drop_order(shipper_id: int, order_id: int) -> bool:
    # Check if the order is in the shipper
    if not redis_client.sismember(f'shipper:{shipper_id}', order_id):
        return False
    order = redis_client.hgetall(f'order:{order_id}')
    if order:
        order['status'] = OrderStatus.Deliverd.value
        redis_client.hmset(f'order:{order_id}', order)
    # Remove the order from the shipper
    redis_client.srem(f'shipper:{shipper_id}', order_id)
    # If all the orders are removed from the shipper, remove the shipper
    if not redis_client.scard(f'shipper:{shipper_id}'):
        redis_client.delete(f'shipper:{shipper_id}')
    return True

def pickup_order(shipper_id: int, order_id: int) -> bool:
    if not redis_client.sismember(f'shipper:{shipper_id}', order_id):
        return False
    order = redis_client.hgetall(f'order:{order_id}')
    if order:
        order['status'] = OrderStatus.Ongoing.value
        redis_client.hmset(f'order:{order_id}', order)
    # Add the order to the shipper if not already in the shipper
    redis_client.sadd(f'shipper:{shipper_id}', order_id)
    return True