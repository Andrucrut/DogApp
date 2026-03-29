from fastapi import APIRouter

from app.api.endpoints.internal import router as internal_router
from app.api.endpoints.notifications import router as notifications_router

api_router = APIRouter()
api_router.include_router(notifications_router)
api_router.include_router(internal_router)
