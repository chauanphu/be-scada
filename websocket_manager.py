import enum
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from redis_client import client as redis_client

class WebSocketManager:
    def __init__(self):
        # Maintain a dictionary where each unit_id maps to a list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, unit_id: str):
        await websocket.accept()
        unit_id = str(unit_id)
        # If the unit_id doesn't exist, create an entry for it
        if unit_id not in self.active_connections:
            self.active_connections[unit_id] = []
        self.active_connections[unit_id].append(websocket)
        previous_status = redis_client.get(unit_id)
        if previous_status:
            await websocket.send_text(previous_status.decode('utf-8'))

    def disconnect(self, websocket: WebSocket, unit_id: str):
        # Remove the websocket from the list of connections for this unit_id
        self.active_connections[str(unit_id)].remove(websocket)
        # If no more connections exist for this unit_id, delete the entry
        if not self.active_connections[str(unit_id)]:
            del self.active_connections[str(unit_id)]

    async def send_private_message(self, message: str, unit_id: str):
        unit_id = str(unit_id)
        # Send the message only to connections for the specified unit_id
        if unit_id in self.active_connections:
            for connection in self.active_connections[unit_id]:
                await connection.send_text(message)

class NOTI_TYPE (enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"
    CRITICAL = "CRITICAL"

class Notification:
    def __init__(self, message: str, type: NOTI_TYPE):
        self.message = message
        self.type = type

    def to_json(self):
        return {
            "message": self.message,
            "type": self.type.value
        }

class NotificationManager:
    def __init__(self):
        self.notifications: list[Notification] = []
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # Add the websocket to the set of active connections
        await websocket.accept()
        self.active_connections.append(websocket)
        if self.get_notifications():
            await websocket.send_json(self.get_notifications())

    async def disconnect(self, websocket: WebSocket):
        # Remove the websocket from the set of active connections
        self.active_connections.remove(websocket)

    def add_notification(self, notification: Notification):
        self.notifications.append(notification)

    def remove_notification(self, notification: Notification):
        self.notifications.remove(notification)

    def get_notifications(self):
        return [notification.to_json() for notification in self.notifications]

    def clear_notifications(self):
        self.notifications = []

    async def broadcast_all(self):
        notifications = self.get_notifications()
        for connection in self.active_connections:
            await connection.send_json(notifications)

    async def broadcast(self, notification: Notification):
        for connection in self.active_connections:
            await connection.send_json([notification.to_json()])

    async def send_notification(self, notification: Notification):
        self.add_notification(notification)
        await self.broadcast(notification)
        
# Initialize the WebSocket manager
manager = WebSocketManager()
notification_manager = NotificationManager()

async def websocket_endpoint(websocket: WebSocket, unit_id: str):
    await manager.connect(websocket, unit_id)
    try:
        while True:
            await websocket.receive_text()  # Keeps the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, unit_id)

async def notification(websocket: WebSocket):
    await notification_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)