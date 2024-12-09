from enum import Enum
import paho.mqtt.client as mqtt
from decouple import config
import json

class MQTTClient(mqtt.Client):
    HOST: str
    PORT: int

    def __init__(self, host=None, port=None, *args, **kwargs):
        super().__init__(mqtt.CallbackAPIVersion.VERSION2)
        port = int(port) if port is not None else None
        # GET MQTT_HOST_NAME FROM ENVIRONMENT VARIABLE
        assert host is not None, "Host must be set"
        assert port is not None, "Port must be set"
        assert isinstance(port, int), f"Port must be an integer, port is {port}"
        self.HOST = host
        self.PORT = port
        print(f"MQTTClient initialized with host: {self.HOST}, port: {self.PORT}")

    def on_connect(self, client, userdata, flags, rc, properties):
        print("Connected with result code "+str(rc))

    # def on_publish(self, client, userdata, mid):
    #     print("Published message", mid)

    def connect(self):
        print(f"Connecting to {self.HOST}:{self.PORT}")
        super().connect(self.HOST, self.PORT, 60)

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
