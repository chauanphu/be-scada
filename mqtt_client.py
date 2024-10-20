from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import regex as re
import json
import asyncio
import logging
import os
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

# Ensure the /log directory exists
# Get the current directory
current_directory = os.getcwd()
log_directory = os.path.join(current_directory, 'log')

if not os.path.exists(log_directory):
    print("Creating log directory:", log_directory)
    os.makedirs(log_directory)
print(os.path.join(log_directory, 'connection.txt'))
# Configure logging
logging.basicConfig(
    filename=os.path.join(log_directory, 'connection.txt'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Client(mqtt_client.Client):
    def __init__(self, client_id=MQTT_CLIENT_ID):
        super().__init__(mqtt_client.CallbackAPIVersion.VERSION2)
        self.HOST = MQTT_BROKER
        self.PORT = MQTT_PORT
        self.ID = MQTT_CLIENT_ID
        print("Initiating...")
        print(f"Host: {self.HOST}, Port: {self.PORT}, ID: {self.ID}")
        self.incoming = {
            "status": self.handle_status,
            "alive": self.handle_connection,
        }

    def connect(self, keepalive=60):
        print("Connecting...")
        super().connect(self.HOST, self.PORT, keepalive)

    def handle_status(self, unit_id, payload):
        body = json.loads(payload)
        status = Status(
            unit_id=unit_id,
            time=datetime.fromtimestamp(body["time"]),
            power=body["power"],
            current=body["current"],
            voltage=body["voltage"],
            toggle=body.get("toggle", False),  # Default to True if not provided
            gps_log=body["gps_log"],
            gps_lat=body["gps_lat"],
            power_factor=body["power_factor"],
            frequency=body["frequency"],
            total_energy=body["total_energy"]
        )
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
                "total_energy": status.total_energy,
                "status": "online",
                "time": status.time.isoformat()
            })
            new_status = Model_Status(
                time=datetime.now(),
                unit_id=status.unit_id,
                power=status.power,
                current=status.current,
                voltage=status.voltage,
                toggle=status.toggle,
                power_factor=status.power_factor,
                frequency=status.frequency,
                total_energy=status.total_energy
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

    def handle_connection(self, unit_id, payload):
        if payload == "online":
            self.handle_device_online(unit_id)
        elif payload == "offline":
            self.handle_device_offline(unit_id)

    def handle_device_online(self, unit_id):
        # Update the device status to online
        session = SessionLocal()
        try:
            status = {
                "status": "online",
                "time": datetime.now().isoformat()
            }
            redis_client.set(unit_id, json.dumps(status))
            print(f"Device {unit_id} is online")
            logging.info(f"Device {unit_id} is online")
            asyncio.run(manager.send_private_message(json.dumps(status), unit_id))
        except Exception as e:
            print(f"Error handling device online: {e}")
        finally:
            session.close()

    def handle_device_offline(self, unit_id):
        # Update the device status to offline
        session = SessionLocal()
        try:
            status = {
                "status": "offline",
                "time": datetime.now().isoformat()
            }
            redis_client.set(unit_id, json.dumps(status))
            print(f"Device {unit_id} is offline")
            logging.info(f"Device {unit_id} is offline")
            asyncio.run(manager.send_private_message(json.dumps(status), unit_id))
        except Exception as e:
            print(f"Error handling device offline: {e}")
        finally:
            session.close()

    ## Override
    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        print(f"Connected with result code {reason_code}")
        logging.info(f"MQTT client connected with result code {reason_code}")
        # Subscribe to device status topics
        self.subscribe("unit/+/status")

    def on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        print(f"Disconnected with result code {reason_code}")
        logging.info(f"MQTT client disconnected with result code {reason_code}")

    def on_message(self, client, userdata, message):
        try:
            # Extract information from the topic: unit/{id}/status
            topic = message.topic
            match = re.match(r"unit/(\w+)/(status|alive)", topic)
            if match:
                unit_id = match.group(1)
                payload = message.payload.decode('utf-8')
                if payload == "offline":
                    # Handle device offline
                    self.handle_device_offline(unit_id)
                elif payload == "online":
                    # Handle device online
                    self.handle_device_online(unit_id)
                else:
                    # Assume payload is JSON
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