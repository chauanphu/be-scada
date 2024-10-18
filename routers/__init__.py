from fastapi import APIRouter

from .auth import router as auth_router
from .cluster_router import router as cluster_router
from .status_router import router as status_router
from .user_router import router as user_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(cluster_router)
api_router.include_router(status_router)