from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_internal
from app.db.session import get_db
from app.schemas.wallet import SettlementRead
from app.services.settlement import settle_booking_wallet

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal)],
)


@router.post(
    "/settlements/bookings/{booking_id}",
    response_model=SettlementRead,
)
async def settle_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SettlementRead:
    ok, err, meta = await settle_booking_wallet(db, booking_id)
    if not ok:
        if err == "insufficient_balance":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="insufficient_balance",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err or "settlement_failed",
        )
    return SettlementRead(
        ok=True,
        already_settled=bool(meta.get("already_settled")),
        error=None,
    )
