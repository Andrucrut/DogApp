from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_internal
from app.db.session import get_db
from app.db_crud.booking_crud import crud_booking
from app.db_crud.walker_crud import crud_walker
from app.models.booking import BookingStatus
from app.schemas.base import BaseModel

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal)])


class BookingActorsResponse(BaseModel):
    owner_id: UUID
    walker_user_id: UUID | None = None
    status: BookingStatus


class BookingPaymentContextResponse(BaseModel):
    owner_id: UUID
    walker_user_id: UUID | None = None
    walker_profile_id: UUID | None = None
    status: BookingStatus
    price: str
    currency: str = "RUB"


class BookingReviewContextResponse(BaseModel):
    owner_id: UUID
    walker_profile_id: UUID | None = None
    walker_user_id: UUID | None = None
    status: BookingStatus
    eligible: bool


class ApplyReviewRatingBody(BaseModel):
    rating: int


@router.get("/bookings/{booking_id}/actors", response_model=BookingActorsResponse)
async def booking_actors(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BookingActorsResponse:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    walker = (
        await crud_walker.get(db, booking.walker_id) if booking.walker_id else None
    )
    return BookingActorsResponse(
        owner_id=booking.owner_id,
        walker_user_id=walker.user_id if walker else None,
        status=booking.status,
    )


@router.get("/bookings/{booking_id}/payment-context", response_model=BookingPaymentContextResponse)
async def booking_payment_context(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BookingPaymentContextResponse:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    walker = (
        await crud_walker.get(db, booking.walker_id) if booking.walker_id else None
    )
    return BookingPaymentContextResponse(
        owner_id=booking.owner_id,
        walker_user_id=walker.user_id if walker else None,
        walker_profile_id=walker.id if walker else None,
        status=booking.status,
        price=str(booking.price),
    )


@router.get("/bookings/{booking_id}/review-context", response_model=BookingReviewContextResponse)
async def booking_review_context(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BookingReviewContextResponse:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    walker = (
        await crud_walker.get(db, booking.walker_id) if booking.walker_id else None
    )
    eligible = booking.status == BookingStatus.COMPLETED
    return BookingReviewContextResponse(
        owner_id=booking.owner_id,
        walker_profile_id=walker.id if walker else None,
        walker_user_id=walker.user_id if walker else None,
        status=booking.status,
        eligible=eligible,
    )


@router.post("/walkers/{walker_id}/apply-review-rating")
async def apply_review_rating(
    walker_id: UUID,
    body: ApplyReviewRatingBody,
    db: AsyncSession = Depends(get_db),
) -> dict:
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_rating")
    walker = await crud_walker.get(db, walker_id)
    if not walker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    n = walker.reviews_count
    new_n = n + 1
    new_avg = (walker.rating * n + float(body.rating)) / new_n if n else float(body.rating)
    await crud_walker.update(
        db,
        walker,
        {"rating": new_avg, "reviews_count": new_n},
    )
    return {"rating": new_avg, "reviews_count": new_n}
