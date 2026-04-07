from fastapi import APIRouter

from app.api.endpoints.internal_settlement import router as internal_settlement_router
from app.api.endpoints.payment import router as payment_router
from app.api.endpoints.wallet_ops import router as wallet_router
from app.api.endpoints.wallet_ops import withdrawals_router

api_router = APIRouter()
api_router.include_router(payment_router)
api_router.include_router(wallet_router)
api_router.include_router(withdrawals_router)
api_router.include_router(internal_settlement_router)
