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
        previous_status = redis_client.get(unit_id).decode('utf-8')
        if previous_status:
            print(f"Pinging previous status to unit {previous_status}")
            await websocket.send_text(previous_status)

    def disconnect(self, websocket: WebSocket, unit_id: str):
        # Remove the websocket from the list of connections for this unit_id
        self.active_connections[str(unit_id)].remove(websocket)
        # If no more connections exist for this unit_id, delete the entry
        if not self.active_connections[str(unit_id)]:
            del self.active_connections[str(unit_id)]

    async def send_private_message(self, message: str, unit_id: str):
        # Send the message only to connections for the specified unit_id
        if unit_id in self.active_connections:
            for connection in self.active_connections[unit_id]:
                await connection.send_text(message)

# Initialize the WebSocket manager
manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket, unit_id: str):
    await manager.connect(websocket, unit_id)
    try:
        while True:
            await websocket.receive_text()  # Keeps the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, unit_id)