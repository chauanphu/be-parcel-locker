from enum import Enum
import paho.mqtt.client as mqtt
from decouple import config
import json

class MQTTClient(mqtt.Client):
    host: str
    port: int

    def __init__(self, host=None, port=None, *args, **kwargs):
        super().__init__(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")
        self.tls_set()
        # GET MQTT_HOST_NAME FROM ENVIRONMENT VARIABLE
        if host is None or port is None:
            raise ValueError("Host and port must be set")
        self.host = host
        self.port = 443

    def on_connect(self, client, userdata, flags, rc, properties):
        print("Connected with result code "+str(rc))

    # def on_publish(self, client, userdata, mid):
    #     print("Published message", mid)

    def connect(self):
        if self.host is None or self.port is None:
            raise ValueError("Host and port must be set")
        print(f"Connecting to {self.host}:{self.port}")
        super().connect(self.host, self.port, 60)

class Request(Enum):
    PRINT_QR = "print_qr"
    UNLOCK = "open"

class LockerClient:
    def __init__(self, mqtt_client: MQTTClient):
        self.mqtt_client = mqtt_client

    def print_qr(self, locker_id: int, order_id: int, code: str):
        payload = {
            "request": Request.PRINT_QR.value,
            "order_id": order_id,
            "OTP": code
        }
        # Encode the payload as a JSON string
        payload = json.dumps(payload)
        self.mqtt_client.publish(f"locker/{locker_id}", payload)

    def unlock(self, locker_id: int, cell_id: int):
        payload = {
            "request": Request.UNLOCK.value,
        }
        payload = json.dumps(payload)
        self.mqtt_client.publish(f"locker/{locker_id}/cell/{cell_id}", payload)
    
MQTT_HOST_NAME = config("MQTT_HOST_NAME")
MQTT_PORT = config("MQTT_PORT")

mqtt_client = MQTTClient(host=MQTT_HOST_NAME, port=MQTT_PORT)
mqtt_client.connect()
mqtt_client.loop_start()
locker_client = LockerClient(mqtt_client)
