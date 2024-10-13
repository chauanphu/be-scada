from fastapi import FastAPI
from mqtt import client
from routers import api_router
from database import setup

def create_app() -> FastAPI:
    app = FastAPI()
    client.connect()
    client.subscribe("unit/+/status")
    client.loop_start()
    app.include_router(api_router)
    return app