# websocket.py
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
from fastapi.websockets import WebSocketState
from sqlalchemy.orm import Session
from auth.utils import get_current_user
from database.session import get_db
from fastapi import Depends
import json
from models.order import Order as OrderModel
from states.shipment import assign_orders_to_shipper, get_orders_by_shipper, deque_route, update_location, Route, track_order

router = APIRouter()

class ConnetionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        # Accept connection
        await websocket.accept()
        # Create a new connection for the user if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def send_to(self, message: str, user_id: int):
        await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

class PushNotiManager(ConnetionManager):
    def __init__(self):
        super().__init__()
    async def notify_new_order(self, user_id, message: str, order_id: int):
        # Stringify the new order to JSON
        new_order = json.dumps({
            "type": "notification",
            "data": {
                "order_id": order_id,
                "message": message
            }
        })
        
        await self.send_to(new_order, user_id)

    async def send_message(self, user_id: int, message: str):
        await self.send_to(json.dumps({"type": "notification", "data": message}), user_id)

class LiveOrderManager(ConnetionManager):
    def __init__(self):
        self.viewers: Dict[int, List[WebSocket]] = {}  # order_id -> list of viewing websockets
    
    def get_location(self, order_id: int):
        latitude, longitude = track_order(order_id=order_id)
        if latitude is None or longitude is None:
            return None, None
        return latitude, longitude

    def format_location(self, order_id: int, latitude: float, longitude: float):
        return json.dumps({
            "type": "location_update",
            "data": {
                "order_id": order_id,
                "latitude": latitude,
                "longitude": longitude
            }
        })

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

    async def broadcast_location(self, order_id: int, latitude: float, longitude: float):
        if order_id in self.viewers:
            update = self.format_location(order_id, latitude, longitude)
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

class ShipperNotiManager(ConnetionManager):
    def __init__(self, _liveOrderManager: LiveOrderManager):
        super().__init__()
        self.liveOrderManager = _liveOrderManager

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    async def notify_new_order(self, shipper_id, new_order: Route):
        # Stringify the new order to JSON
        new_order = json.dumps({
            "type": "new_order",
            "data": new_order
        })
        await self.send_to(new_order, shipper_id)

    async def dequeue_order(self, shipper_id: int):
        route: Route = deque_route()
        if not route:
            return
        # Notify the shipper about the new order
        assign_orders_to_shipper(shipper_id, route)
        await self.notify_new_order(shipper_id, route)
        # Add the order to the shipper's list of orders using redis

pushNotiManager = PushNotiManager()
liveOrderManager = LiveOrderManager()
shipperNotiManager = ShipperNotiManager(liveOrderManager)

# Websocker for tracking the order in real-time
@router.websocket("/tracking/{order_id}")
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
        # Get order from database
        order = db.query(OrderModel).filter(OrderModel.order_id == order_id).first()
        if not order:
            await websocket.close(code=1008, reason="Order not found")
            return
        # Check if user has permission to view/update this order
        is_authorised = user.user_id in [order.sender_id, order.recipient_id]
        if not is_authorised:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Connect based on role
        try:
            await liveOrderManager.connect_viewer(websocket, order_id)
            latitude, longitude = liveOrderManager.get_location(order_id)
            await liveOrderManager.broadcast_location(order_id, latitude, longitude)
            while True:
                await websocket.receive_text()

        except WebSocketDisconnect:
            liveOrderManager.disconnect(websocket)
            
    except HTTPException:
        if not websocket.client_state.disconnected:
            await websocket.close(code=1008, reason="Authentication failed")
    except Exception as e:
        if not websocket.client_state.disconnected:
            await websocket.close(code=1011, reason="Internal server error")

# Websocket to send notifications to the customer
@router.websocket("/customer")
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
        
        try:
            # Connect with user ID
            await pushNotiManager.connect(websocket, user_id=user.user_id)
            while True:
                await pushNotiManager.send_message(user.user_id, "You have a new notification")
                await websocket.receive_text()
        except WebSocketDisconnect:
            pushNotiManager.disconnect(user.user_id)
            
    except HTTPException:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1008, reason="Authentication failed")
    except Exception as e:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1011, reason="Internal server error")
            logging.error(str(e))
        
# Websocket only for shipper, to notify new
@router.websocket("/shipper")
async def websocket_notifications(
    websocket: WebSocket,
    db: Session = Depends(get_db)
    ):
    try:
        headers = dict(websocket.headers)
        token = headers.get('authorization', '').replace('Bearer ', '')
            
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        # Verify user
        user = get_current_user(token, db)
        # Check if user has permission to view/update this order
        is_shipper = user.role_rel.name == 'shipper'
        
        if not is_shipper:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Connect based on role
        await shipperNotiManager.connect(websocket, user.user_id)
        try:
            # Notify new order
            await shipperNotiManager.dequeue_order(user.user_id)
            while True:
                # Sending notifications to the shipper
                data = await websocket.receive_text()
                data = json.loads(data)
                if data['type'] != 'location_update':
                    continue
                if data['latitude'] is None or data['longitude'] is None:
                    continue
                # Update the location of the shipper and broadcast to all viewers
                update_location(user.user_id, data['latitude'], data['longitude'])
                order_ids = get_orders_by_shipper(user.user_id)
                for order_id in order_ids:
                    await liveOrderManager.broadcast_location(order_id, data['latitude'], data['longitude'])
        except WebSocketDisconnect:
            shipperNotiManager.disconnect(user.user_id)
    except HTTPException as e:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=1008, reason="Authentication failed")
        logging.error(f"HTTP Exception: {str(e)}")
    except Exception as e:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason="Internal server error")
        logging.error(f"Unexpected error: {str(e)}")