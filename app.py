from fastapi import FastAPI
from mqtt_client import client
from routers import api_router
from websocket.ws_router import router as ws_router

def create_app() -> FastAPI:
    app = FastAPI()
    client.connect()
    client.subscribe("unit/+/status")
    client.subscribe("unit/+/command")
    client.loop_start()
    app.include_router(api_router)
    app.include_router(ws_router)
    return app