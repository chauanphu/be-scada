from fastapi import APIRouter

from .auth import router as auth_router
from .cluster_router import router as cluster_router
from .status_router import router as status_router
from .user_router import router as user_router
from .audit_router import router as audit_router
from .file_router import router as file_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(cluster_router)
api_router.include_router(status_router)
api_router.include_router(audit_router)
api_router.include_router(file_router)