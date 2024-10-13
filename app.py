from fastapi import FastAPI
from mqtt_client import client
from routers import api_router

def create_app() -> FastAPI:
    app = FastAPI()
    client.connect()
    client.subscribe("unit/+/status")
    client.loop_start()
    app.include_router(api_router)
    return app