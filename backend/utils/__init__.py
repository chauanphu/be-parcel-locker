from decouple import config
from .mqtt import LockerClient, MQTTClient

MQTT_HOST_NAME = config("MQTT_HOST_NAME")
MQTT_PORT = config("MQTT_PORT")

mqtt_client = MQTTClient(host=MQTT_HOST_NAME, port=MQTT_PORT)
mqtt_client.connect()
mqtt_client.loop_start()
locker_client = LockerClient(mqtt_client)
