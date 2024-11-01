from datetime import datetime
from enum import Enum
import psycopg2
import regex as re
import json
import asyncio
import logging
import os
# Database & Caching
from database import SessionLocal
from models.Task import TaskType, TaskTypeEnum
from redis_client import client as redis_client
# MQTT, Websocket
from models.Status import Status as Model_Status
from models.unit import Unit
from paho.mqtt import client as mqtt_client
from utils import add_task
from websocket_manager import manager, notification_manager, NOTI_TYPE, Notification
from config import MQTT_BROKER, MQTT_PORT, MQTT_CLIENT_ID, POWERLOST_THRESHOLD


class COMMAND(Enum):
    TOGGLE = "TOGGLE"
    SCHEDULE = "SCHEDULE"
    AUTO = "AUTO"

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
        self.ttl = 60 * 5 # 5 minutes

    def command(self, unit_id, command: COMMAND, payload):
        # Get mac address from database
        with SessionLocal() as session:
            unit = session.query(Unit).filter(Unit.id == unit_id).first()
            if not unit:
                print("Unit not found")
                return
            mac_address = unit.mac
        body = {
            "command": command.value,
        }
        if command in COMMAND:
            body["payload"] = payload
        else:
            print("Invalid command")
            return
        # Stringify the body
        body = json.dumps(body)
        print(f"Command: {command}, Payload: {body}")
        topic = f"unit/{mac_address}/command"
        # Convert the body to JSON String
        self.publish(topic, body)

    def connect(self, keepalive=60):
        print("Connecting...")
        super().connect(self.HOST, self.PORT, keepalive)

    def handle_status(self, unit_id, payload):
        body = json.loads(payload)
        # Store the status in the database
        session = SessionLocal()
        try:
            # Check if the timestamp already exists
            time = datetime.fromtimestamp(body['time'])
            status = session.query(Model_Status).filter(Model_Status.unit_id == unit_id, Model_Status.time == time).first()
            
            if status:
                print("Status already exists")
                return
            new_status = Model_Status(
                unit_id=unit_id,
                time=datetime.fromtimestamp(body['time']),
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
            # Check for powerlost and add task
            if bool(body["toggle"]) and float(body["power"]) < POWERLOST_THRESHOLD:
                add_task(unit_id, TaskTypeEnum.POWER_OFF)

            # Check if hour_on, hour_off, minute_on, minute_off is different from the previous status in Redis
            prev_status = redis_client.get(f"device:{unit_id}")
            if prev_status:
                prev_status = json.loads(prev_status)
                hour_on = prev_status.get("hour_on")
                hour_off = prev_status.get("hour_off")
                minute_on = prev_status.get("minute_on")
                minute_off = prev_status.get("minute_off")

                if hour_on != body.get("hour_on") or minute_on != body.get("hour_off"):
                    new_on_time = f"{body['hour_on']}:{body['minute_on']}"
                    session.query(Unit).filter(Unit.id == unit_id).update({"on_time": new_on_time})
                if hour_off != body.get("hour_off") or minute_off != body.get("minute_off"):
                    new_off_time = f"{body['hour_off']}:{body['minute_off']}"
                    session.query(Unit).filter(Unit.id == unit_id).update({"off_time": new_off_time})
                session.commit()

            # Store the status in Redis
            body = json.dumps(body)
            redis_client.setex(f"device:{unit_id}", self.ttl, body)
            asyncio.run(manager.send_private_message(body, unit_id))
        # Duplicate timestamp
        except psycopg2.errors.UniqueViolation:
            print("Duplicate timestamp")
            session.rollback()
        except Exception as e:
            print(f"Error storing status: {e}")
            session.rollback()
        finally:
            session.close()

    def handle_connection(self, unit_id: int, payload):
        unit_name = payload["name"]
        body = payload["body"]

        if body != "1" and body != "0":
            print("Invalid connection status")
            return
        status = {
            "alive": body,
            "time": datetime.now().isoformat()
        }
        # Only set the status in Redis if the device is disconnected
        print(f"Device {unit_id} is {body}")
        if body == "0":
            redis_client.setex(f"device:{unit_id}", self.ttl, json.dumps(status))
            notification = Notification(
                type=NOTI_TYPE.CRITICAL,
                message=f"Thiết bị {unit_name} đã mất kết nối"
            )
            add_task(unit_id, TaskTypeEnum.DISCONNECTION)
            asyncio.run(manager.send_private_message(json.dumps(status), unit_id))
            # asyncio.run(notification_manager.send_notification(notification))
        else:
            notification = Notification(
                type=NOTI_TYPE.INFO,
                message=f"Thiết bị {unit_name} đã kết nối"
            )
            asyncio.run(notification_manager.send_notification(notification))

            # Sync the schedule to the device
            try:
                with SessionLocal() as session:
                    unit = session.query(Unit).filter(Unit.id == unit_id).first()
                    if not unit:
                        print("Unit not found")
                        return
                    # Convert from datetime.time to string
                    on_time = unit.on_time.strftime("%H:%M")
                    off_time = unit.off_time.strftime("%H:%M")
                    schedule = {
                        "hour_on": on_time.split(":")[0],
                        "minute_on": on_time.split(":")[1],
                        "hour_off": off_time.split(":")[0],
                        "minute_off": off_time.split(":")[1]
                    }
                    self.command(unit_id, COMMAND.SCHEDULE, schedule)
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                session.close()

    ## Override
    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        print(f"Connected with result code {reason_code}")
        logging.info(f"MQTT client connected with result code {reason_code}")
        # Subscribe to device status topics
        self.subscribe("unit/+/status")
        self.subscribe("unit/+/alive")

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
                        print("Unit not found: ", mac_address)
                        return
                    unit_id = unit.id
                    body = message.payload.decode("utf-8")
                    if _type == "status":
                        self.incoming["status"](unit_id, body)
                    elif _type == "alive":
                        payload = {
                            "name": unit.name,
                            "body": body
                        }
                        self.incoming["alive"](unit_id, payload)
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