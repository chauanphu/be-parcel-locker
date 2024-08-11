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
    
class dataGPS(BaseModel):
    latitude: float
    longitude: float

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
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received data: {data}")
            try:
                gps_data = GPSData(**data)
                location_data_list.append(gps_data)
                await websocket.send_json({"status": "received", "data": data})
            except ValueError as e:
                print(f"Error parsing data: {e}")
                await websocket.send_json({"status": "error", "message": str(e)})
    except WebSocketDisconnect:
        print("Client disconnected")
