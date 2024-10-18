from fastapi import WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app import create_app
import uvicorn
from websocket_manager import websocket_endpoint

app = create_app()

# WebSocket route for real-time traffic monitoring
@app.websocket("/ws/unit/{unit_id}/status")
async def websocket_route(websocket: WebSocket, unit_id: int):
    await websocket_endpoint(websocket, unit_id)
        
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    # Add more origins as needed
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