from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.payment_crud import crud_payment
from app.models.payment import PaymentStatus
from app.schemas.payment import MockConfirmBody, PaymentIntentCreate, PaymentRead
from app.services.booking_client import fetch_payment_context

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/intents", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_intent(
    body: PaymentIntentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> PaymentRead:
    ctx = await fetch_payment_context(body.booking_id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="booking_unavailable",
        )
    if ctx.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if ctx.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="booking_not_completed",
        )
    if not ctx.walker_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no_walker_assigned",
        )

    existing = await crud_payment.get_by_booking_id(db, body.booking_id)
    if existing:
        if existing.status == PaymentStatus.SUCCEEDED:
            return PaymentRead.model_validate(existing)
        if existing.payer_owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="conflict")
        return PaymentRead.model_validate(existing)

    payment = await crud_payment.create(
        db,
        {
            "booking_id": body.booking_id,
            "payer_owner_id": ctx.owner_id,
            "beneficiary_walker_user_id": ctx.walker_user_id,
            "amount": ctx.price,
            "currency": ctx.currency,
            "status": PaymentStatus.PENDING,
            "external_payment_id": f"mock_{uuid4()}",
        },
    )
    return PaymentRead.model_validate(payment)


@router.post("/{payment_id}/confirm", response_model=PaymentRead)
async def confirm_mock_payment(
    payment_id: UUID,
    body: MockConfirmBody,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> PaymentRead:
    payment = await crud_payment.get(db, payment_id)
    if not payment or payment.payer_owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if payment.status == PaymentStatus.SUCCEEDED:
        return PaymentRead.model_validate(payment)
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_state")

    if body.simulate_failure:
        updated = await crud_payment.update(
            db,
            payment,
            {
                "status": PaymentStatus.FAILED,
                "failure_reason": "mock_provider_declined",
            },
        )
    else:
        updated = await crud_payment.update(
            db,
            payment,
            {"status": PaymentStatus.SUCCEEDED, "failure_reason": None},
        )
    return PaymentRead.model_validate(updated)


@router.get("/me", response_model=list[PaymentRead])
async def list_my_payments(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = 50,
    offset: int = 0,
) -> list[PaymentRead]:
    rows = await crud_payment.list_for_user(db, user_id, limit=limit, offset=offset)
    return [PaymentRead.model_validate(r) for r in rows]


@router.get("/by-booking/{booking_id}", response_model=PaymentRead)
async def get_by_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> PaymentRead:
    payment = await crud_payment.get_by_booking_id(db, booking_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if user_id not in (payment.payer_owner_id, payment.beneficiary_walker_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return PaymentRead.model_validate(payment)
