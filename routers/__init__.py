from fastapi import APIRouter
from .auth import router as auth_router
from .cluster_router import router as cluster_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(cluster_router)