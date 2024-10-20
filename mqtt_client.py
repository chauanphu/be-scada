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
from models.unit import Unit
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
        print(body)
        # Store the status in the database
        session = SessionLocal()
        try:
            new_status = Model_Status(
                unit_id=unit_id,
                time=datetime.now(),
                power=body['power'],
                current=body['current'],
                voltage=body['voltage'],
                toggle=body['toggle'],
                power_factor=body['power_factor'],
                frequency=body['frequency'],
                total_energy=body['total_energy']
            )
            session.add(new_status)
            session.commit()
            # Store the status in Redis
            body = json.dumps(body)
            redis_client.set(unit_id, body)
            print("Status stored successfully.")
            asyncio.run(manager.send_private_message(body, unit_id))
            print("Broadcasted")
        except Exception as e:
            print(f"Error storing status: {e}")
            session.rollback()
        finally:
            session.close()

    def handle_connection(self, unit_id, payload):
        if payload != "1" and payload != "0":
            print("Invalid connection status")
            return
        status = {
            "status": payload,
            "time": datetime.now().isoformat()
        }
        redis_client.set(unit_id, json.dumps(status))
        print(f"Device {unit_id} is {payload}")
        logging.info(f"Device {unit_id} is {payload}")
        asyncio.run(manager.send_private_message(json.dumps(status), unit_id))

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
                mac_address, _type = match.groups()
                # Get unit id from database by mac address
                session = SessionLocal()
                try:
                    unit = session.query(Unit).filter(Unit.mac == mac_address).first()
                    if not unit:
                        print("Unit not found")
                        return
                    unit_id = unit.id
                    if _type in self.incoming:
                        payload = message.payload.decode('utf-8')                        
                        self.incoming[_type](unit_id, payload)
                    else:
                        print("Invalid message type", _type)
                except Exception as e:
                    print(f"An error occurred: {e}")
                finally:
                    session.close()
            else:
                print("Invalid topic", topic)
        except json.JSONDecodeError:
            print("Failed to decode JSON payload")
        except KeyError as e:
            print(f"Missing key in payload: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

client = Client()