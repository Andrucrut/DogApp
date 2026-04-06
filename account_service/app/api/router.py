from fastapi import APIRouter
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.role import router as role_router
from app.api.endpoints.user import router as user_router
from app.api.endpoints.admin import router as admin_router
from app.api.endpoints.internal_profiles import router as internal_profiles_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(role_router)
api_router.include_router(user_router)
api_router.include_router(admin_router)
api_router.include_router(internal_profiles_router)


