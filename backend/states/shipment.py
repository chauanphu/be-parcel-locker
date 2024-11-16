from typing import List
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
    def __init__(self, locker_id: int, latitude: float, longitude: float):
        self.locker_id = locker_id
        self.latitude = latitude
        self.longitude = longitude
        self.pickup_orders: List[Order] = []
        self.dropoff_orders: List[Order] = []
        self.__dict__ = {
            "locker_id": self.locker_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "pickup_orders": [],
            "dropoff_orders": []
        }
    
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
      
def set_route(route: Route):
    """
    This function sets the route of the shipper to Redis
    """
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