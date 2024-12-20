from fastapi import WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app import create_app
import uvicorn
from websocket_manager import websocket_endpoint, notification

app = create_app()

# WebSocket route for real-time traffic monitoring
@app.websocket("/ws/unit/{unit_id}/status")
async def websocket_route(websocket: WebSocket, unit_id: int):
    await websocket_endpoint(websocket, unit_id)

# Websocket route for notifications
@app.websocket("/ws/notifications")
async def websocket_route(websocket: WebSocket):
    try:
        token = websocket.query_params.get('token')
        if not token:
            await websocket.close(code=1008, reason="Token is required")
            return
        await notification(websocket, token)
    except Exception as e:
        await websocket.close(code=1008, reason=str(e))
    
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # VITE dev server
    "https://scada.chaugiaphat.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)