from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from paho.mqtt import client as mqtt_client
from decouple import config
import regex as re
import json
from models.Status import Status as Model_Status

# Database
from database.__init__ import SessionLocal

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
    unit_id: int
    # Time
    time: datetime
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
        # Store the status in the database
        session = SessionLocal()
        try:
            new_status = Model_Status(
                time=status.time,
                unit_id=status.unit_id,
                power = status.power,
                current = status.current,
                voltage = status.voltage
            )
            session.add(new_status)
            session.commit()
            print("Status stored successfully.")
        except Exception as e:
            print(f"Error storing status: {e}")
            session.rollback()
        finally:
            session.close()

    def handle_command(self, command: COMMAND):
        # Handle the command
        print(f"Command received: {command}")
        # Implement the logic to handle the command
        pass

    ## Override
    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")

    def on_publish(self, client, userdata, mid, reason_code, properties):
        print(f"Published `{mid}` message")

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Disconnected with result code {reason_code}")
        
    def on_message(self, client, userdata, message):
        # Extract information from the topic: rpi/unit/{id}/status or rpi/unit/{id}/command
        topic = message.topic
        # Acion is either status or command
        match = re.match(r"unit/(\w+)/(?:status|command)", topic)
        if match:
            unit_id = match.group(1)
            body = json.loads(message.payload)
            # Body of status is power, current, voltage, alive
            # Body of command is command
            if "status" in topic:
                status = Status(
                    time=datetime.now(),
                    unit_id=unit_id, 
                    power=body["power"], 
                    current=body["current"], 
                    voltage=body["voltage"],
                )
                
                self.handle_status(status)
            elif "command" in topic:
                command = COMMAND(body["command"])
                self.handle_command(command)
        else:
            print("Invalid topic", topic)

    def on_subscribe(self, client, userdata, mid, granted_qos, properties):
        print(f"Subscribed to `{mid}` topic")
    
client = Client()