from fastapi import WebSocket
from app import create_app
import uvicorn

from websocket_manager import websocket_endpoint

app = create_app()

# WebSocket route for real-time traffic monitoring
@app.websocket("/ws/unit/{unit_id}/status")
async def websocket_route(websocket: WebSocket, unit_id: int):
    await websocket_endpoint(websocket, unit_id)
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)