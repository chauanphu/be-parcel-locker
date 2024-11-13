# websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
from sqlalchemy.orm import Session
from auth.utils import get_current_user
from database.session import get_db
from fastapi import Depends
from utils.redis import redis_client
import json

router = APIRouter()

class Order:
    """
    This model represents the order of the customer
    """
    def __init__(self, order_id: int, size: str, weight: float):
        self.order_id = order_id
        self.size = size
        self.weight = weight
        self.__dict__ = {
            "order_id": self.order_id,
            "size": self.size,
            "weight": self.weight
        }
    
class Location:
    """
    This model represents the location of the customer
    """
    def __init__(self, location_id: int, latitude: float, longitude: float):
        self.location_id = location_id
        self.latitude = latitude
        self.longitude = longitude
        self.pickup_orders: List[Order] = []
        self.dropoff_orders: List[Order] = []
        self.__dict__ = {
            "location_id": self.location_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "pickup_orders": [order.__dict__ for order in self.pickup_orders],
            "dropoff_orders": [order.__dict__ for order in self.dropoff_orders]
        }

class Route:
    """
    This model represents the shipping route of shipper, which contains the visited location and the pickup/dropoff orders
    """
    def __init__(self) -> None:
        self.visited_locations: List[Location] = []
        self.__dict__ = {
            "visited_locations": [location.__dict__ for location in self.visited_locations]
        }

class ConnetionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        # Create a new connection for the user if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def send_personal_message_to(self, message: str, user_id: int):
        await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

class PushNotiManager(ConnetionManager):
    def __init__(self):
        super().__init__()

    def send_message(self, user_id: int, message: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].send_text(message)

class ShipperNotiManager(ConnetionManager):
    def __init__(self):
        super().__init__()

    def notify_new_order(self, new_order: Route):
        # Stringify the new order to JSON
        new_order = json.dumps({
            "type": "new_order",
            "data": new_order.__dict__
        })
        
        for connection in self.active_connections.values():
            connection.send_text(new_order)

class LiveOrderManager(ConnetionManager):
    def __init__(self):
        self.viewers: Dict[int, List[WebSocket]] = {}  # order_id -> list of viewing websockets
        self.updater: Dict[int, WebSocket] = {}  # order_id -> shipper websocket
    
    def get_location(self, order_id: int):
        latitude = redis_client.hget(f"order:{order_id}", "latitude")
        longitude = redis_client.hget(f"order:{order_id}", "longitude")
        if latitude is None or longitude is None:
            return None, None
        return latitude, longitude

    def update_location(self, order_id: int, latitude: float, longitude: float):
        redis_client.hset(f"order:{order_id}", "latitude", latitude)
        redis_client.hset(f"order:{order_id}", "longitude", longitude)

    async def connect_viewer(self, websocket: WebSocket, order_id: int):
        # Remove viewer from any existing order they might be watching
        for viewers in self.viewers.values():
            if websocket in viewers:
                viewers.remove(websocket)
                break
            
        await websocket.accept()
        if order_id not in self.viewers:
            self.viewers[order_id] = []
        self.viewers[order_id].append(websocket)

    async def connect_updater(self, websocket: WebSocket, order_id: int):
        await websocket.accept()
        self.updater[order_id] = websocket

    async def broadcast_location(self, order_id: int, latitude: float, longitude: float):
        if order_id in self.viewers:
            update = json.dumps({
                "type": "location_update",
                "data": {
                    "order_id": order_id,
                    "latitude": latitude,
                    "longitude": longitude
                }
            })
            for viewer in self.viewers[order_id]:
                try:
                    await viewer.send_text(update)
                except:
                    self.viewers[order_id].remove(viewer)

    async def disconnect(self, websocket: WebSocket):
        # Remove from viewers if present
        for viewers in self.viewers.values():
            if websocket in viewers:
                viewers.remove(websocket)
                break
            
        # Remove from updater if it's a shipper
        for order_id, updater in self.updater.items():
            if websocket == updater:
                del self.updater[order_id]
                break

pushNotiManager = PushNotiManager()
shipperNotiManager = ShipperNotiManager()
liveOrderManager = LiveOrderManager()

# Websocker for tracking the order in real-time
@router.websocket("/ws/tracking/{order_id}")
async def websocket_tracking(
    websocket: WebSocket,
    order_id: int,
    db: Session = Depends(get_db),
):
    try:
        headers = dict(websocket.headers)
        token = headers.get('authorization', '').replace('Bearer ', '')
        
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        # Verify user
        user = get_current_user(token, db)
        
        # Get the order from the database
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            await websocket.close(code=1008, reason="Order not found")
            return
        
        # Check if user has permission to view/update this order
        is_shipper = user.role == "shipper" and order.shipper_id == user.user_id
        is_customer = user.user_id in (order.sender_id, order.receiver_id)
        
        if not (is_shipper or is_customer):
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Connect based on role
        if is_shipper:
            await liveOrderManager.connect_updater(websocket, order_id)
        else:
            await liveOrderManager.connect_viewer(websocket, order_id)
            latitude, longitude = liveOrderManager.get_location(order_id)
            if latitude is not None and longitude is not None:
                await websocket.send_text(json.dumps({
                    "type": "location_update",
                    "data": {
                        "order_id": order_id,
                        "latitude": latitude,
                        "longitude": longitude
                    }
                }))
        try:
            while True:
                data = await websocket.receive_json()
                
                # Only shipper can send location updates
                if is_shipper and "latitude" in data and "longitude" in data:
                    latitude = float(data["latitude"])
                    longitude = float(data["longitude"])
                    await liveOrderManager.broadcast_location(order_id, latitude, longitude)
        except WebSocketDisconnect:
            pass
        except ValueError:
            if is_shipper:
                await websocket.close(code=1008, reason="Invalid location data")
            
    except HTTPException:
        if not websocket.client_state.disconnected:
            await websocket.close(code=1008, reason="Authentication failed")
    except Exception as e:
        if not websocket.client_state.disconnected:
            await websocket.close(code=1011, reason="Internal server error")

# Websocket to send notifications to the customer
@router.websocket("/ws/customer")
async def websocket_notifications(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    try:
        # Get token from headers
        headers = dict(websocket.headers)
        token = headers.get('authorization', '').replace('Bearer ', '')
        
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        # Verify user
        user = get_current_user(token, db)
        
        # Accept connection
        await websocket.accept()
        
        # Connect with user ID
        await pushNotiManager.connect(websocket, user_id=user.user_id)
        
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pushNotiManager.disconnect(user.user_id)
            
    except HTTPException:
        if not websocket.client_state.disconnected:
            await websocket.close(code=1008, reason="Authentication failed")
    except Exception as e:
        if not websocket.client_state.disconnected:
            await websocket.close(code=1011, reason="Internal server error")
        
# Websocket only for shipper, to notify new
@router.websocket("/ws/shipper")
async def websocket_notifications(websocket: WebSocket):
    await pushNotiManager.connect(websocket)
    try:
        while True:
            # Sending notifications to the shipper
            await websocket.receive_text()
    except WebSocketDisconnect:
        pushNotiManager.disconnect(websocket)