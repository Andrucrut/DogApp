from fastapi import APIRouter

from app.api.endpoints.booking import router as booking_router
from app.api.endpoints.address import router as address_router
from app.api.endpoints.dog import router as dog_router
from app.api.endpoints.internal import router as internal_router
from app.api.endpoints.schedule import router as schedule_router
from app.api.endpoints.walker import router as walker_router

api_router = APIRouter()
api_router.include_router(dog_router)
api_router.include_router(walker_router)
api_router.include_router(booking_router)
api_router.include_router(schedule_router)
api_router.include_router(address_router)
api_router.include_router(internal_router)
