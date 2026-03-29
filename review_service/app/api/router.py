from fastapi import APIRouter

from app.api.endpoints.review import router as review_router

api_router = APIRouter()
api_router.include_router(review_router)
