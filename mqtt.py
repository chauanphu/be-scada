from dataclasses import dataclass
from enum import Enum
from paho.mqtt import client as mqtt_client
from decouple import config
import regex as re
import json

# MQTT setup
MQTT_BROKER = config("MQTT_BROKER")
MQTT_PORT = int(config("MQTT_PORT"))
MQTT_CLIENT_ID = config("MQTT_CLIENT_ID")

class COMMAND(Enum):
    ON = "ON"
    OFF = "OFF"
    SCHEDULE = "SCHEDULE"

@dataclass
class Status:
    id: str
    # Power consumption in watts
    power: float
    # Working current in amperes
    current: float
    # Input voltage in volts
    voltage: float
    # Alive
    alive: bool

class Client(mqtt_client.Client):
    def __init__(self, client_id=MQTT_CLIENT_ID):
        super().__init__(mqtt_client.CallbackAPIVersion.VERSION2, client_id)
        self.HOST= MQTT_BROKER
        self.PORT= MQTT_PORT
        self.ID = MQTT_CLIENT_ID
        print("Initiating...")
        print(f"Host: {self.HOST}, Port: {self.PORT}, ID: {self.ID}")

    def connect(self, keepalive=60):
        print("Connecting...")
        super().connect(MQTT_BROKER, MQTT_PORT, keepalive)

    def handle_status(self, status: Status):
        print("Handling status...")

    ## Override
    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")

    def on_publish(self, client, userdata, mid, reason_code, properties):
        print(f"Published `{mid}` message")

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected with result code {rc}")

    def on_message(self, client, userdata, message):
        # Extract information from the topic: rpi/unit/{id}/status, ex: rpi/unit/abe123/status
        topic = message.topic
        match = re.match(r"unit/(\w+)/status", topic)
        if match:
            unit_id = match.group(1)
            body = json.loads(message.payload)
            self.handle_status(Status(unit_id, **body))
        else:
            print("Invalid topic", topic)

    def on_subscribe(self, client, userdata, mid, granted_qos, properties):
        print(f"Subscribed to `{mid}` topic")
    
client = Client()