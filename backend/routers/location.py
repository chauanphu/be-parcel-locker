from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(
    prefix="/location",
    tags=["location"]
)

class GPSData(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    altitude: float = None
    speed: float = None
    accuracy: float = None

# Temporary list to store location data
location_data_list: List[GPSData] = []

@router.post("/", response_model=GPSData)
def receive_location_data(data: GPSData):
    location_data_list.append(data)
    return data

@router.get("/", response_model=List[GPSData])
def get_location_data():
    return location_data_list


# WebSocket endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            gps_data = GPSData(**data)
            location_data_list.append(gps_data)
            await websocket.send_json({"status": "received", "data": data})
    except WebSocketDisconnect:
        print(f"Client {user_id} disconnected")