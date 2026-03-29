from fastapi import APIRouter

from app.api.endpoints.walk import router as walk_router
from app.api.endpoints.ws import router as ws_router

api_router = APIRouter()
api_router.include_router(walk_router)
api_router.include_router(ws_router)
