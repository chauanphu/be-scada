from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import regex as re
import json
import asyncio
# Database & Caching
from database.__init__ import SessionLocal
from redis_client import client as redis_client
# MQTT, Websocket
from models.Status import Status as Model_Status
from paho.mqtt import client as mqtt_client
from websocket_manager import manager
from config import MQTT_BROKER, MQTT_PORT, MQTT_CLIENT_ID


class COMMAND(Enum):
    TOGGLE = "TOGGLE"
    SCHEDULE = "SCHEDULE"

@dataclass
class Status:
    unit_id: int
    time: datetime
    power: float
    current: float
    voltage: float
    toggle: bool
    gps_log: str
    gps_lat: str
    power_factor: float
    frequency: float
    total_energy: float

class Client(mqtt_client.Client):
    def __init__(self, client_id=MQTT_CLIENT_ID):
        super().__init__(mqtt_client.CallbackAPIVersion.VERSION2)
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
            body = json.dumps({
                "power": status.power,
                "current": status.current,
                "voltage": status.voltage,
                "toggle": status.toggle,
                "gps_log": status.gps_log,
                "gps_lat": status.gps_lat,
                "power_factor": status.power_factor,
                "frequency": status.frequency,
                "total_energy": status.total_energy
            })
            new_status = Model_Status(
                time=datetime.now(),
                unit_id=status.unit_id,
                power = status.power,
                current = status.current,
                voltage = status.voltage,
                toggle = status.toggle,
                power_factor = status.power_factor,
                frequency = status.frequency,
                total_energy = status.total_energy
            )
            session.add(new_status)
            session.commit()
            # Store the status in Redis
            redis_client.set(status.unit_id, body)
            
            print("Status stored successfully.")
            asyncio.run(manager.send_private_message(body, status.unit_id))
            
            print("Broadcasted")
        except Exception as e:
            print(f"Error storing status: {e}")
            session.rollback()
        finally:
            session.close()

    ## Override
    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"Disconnected with result code {reason_code}")
        
    def on_message(self, client, userdata, message):
        try:
            # Extract information from the topic: rpi/unit/{id}/status or rpi/unit/{id}/command
            topic = message.topic
            # Action is either status
            match = re.match(r"unit/(\w+)/(?:status)", topic)
            if match:
                unit_id = match.group(1)
                body = json.loads(message.payload)
                # Body of status is power, current, voltage, alive
                # Body of command is command
                if "status" in topic:
                    status = Status(
                        unit_id=unit_id,
                        time=datetime.fromtimestamp(body["time"]),
                        power=body["power"],
                        current=body["current"],
                        voltage=body["voltage"],
                        toggle=body["toggle"],  # Default to True if not provided
                        gps_log=body["gps_log"],
                        gps_lat=body["gps_lat"],
                        power_factor=body["power_factor"],
                        frequency=body["frequency"],
                        total_energy=body["total_energy"]
                    )
                    
                    self.handle_status(status)
            else:
                print("Invalid topic", topic)
        except json.JSONDecodeError:
            print("Failed to decode JSON payload")
        except KeyError as e:
            print(f"Missing key in payload: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
    
client = Client()