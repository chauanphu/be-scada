from fastapi import FastAPI
from mqtt import client
def create_app() -> FastAPI:
    app = FastAPI()
    client.connect()
    return app