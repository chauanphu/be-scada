from fastapi import FastAPI
from database.session import session
from models.Status import Status as Model_Status
from mqtt_client import Status as Mqtt_Status
from mqtt_client import client
from routers import api_router
    
def create_app() -> FastAPI:
    app = FastAPI()
    client.connect()
    client.subscribe("unit/+/status")
    client.subscribe("unit/+/command")
    client.loop_start()
    app.include_router(api_router)
    return app