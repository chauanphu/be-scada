from fastapi import FastAPI
from mqtt_client import client
from routers import api_router
from database.setup import create_default_roles, create_default_admin

def create_app() -> FastAPI:
    app = FastAPI(
        title="SCADA Traffic Light System",
        description="A SCADA system for controlling traffic lights",
        version="0.1.0"
    )
    create_default_roles()
    create_default_admin()
    client.connect()
    client.subscribe("unit/+/status")
    client.loop_start()
    app.include_router(api_router)
    return app