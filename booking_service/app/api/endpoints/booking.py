from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.booking_crud import crud_booking
from app.db_crud.dog_crud import crud_dog
from app.db_crud.walker_crud import crud_walker
from app.models.booking import BookingStatus
from app.schemas.booking import BookingCreate, BookingRead, BookingStatusUpdate
from app.services.outbound import (
    cancel_scheduled_reminders,
    schedule_walk_reminder,
    send_notifications,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _booking_read(b) -> BookingRead:
    return BookingRead.model_validate(b)


@router.get("/me/owner", response_model=list[BookingRead])
async def list_as_owner(
    db: AsyncSession = Depends(get_db),
    owner_id: UUID = Depends(get_current_user_id),
    limit: int = 50,
    offset: int = 0,
) -> list[BookingRead]:
    rows = await crud_booking.list_for_owner(db, owner_id, limit=limit, offset=offset)
    return [_booking_read(b) for b in rows]


@router.get("/me/walker", response_model=list[BookingRead])
async def list_as_walker(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = 50,
    offset: int = 0,
) -> list[BookingRead]:
    walker = await crud_walker.get_by_user_id(db, user_id)
    if not walker:
        return []
    rows = await crud_booking.list_for_walker(db, walker.id, limit=limit, offset=offset)
    return [_booking_read(b) for b in rows]


@router.get("/open", response_model=list[BookingRead])
async def list_open_bookings(
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
    limit: int = 50,
    offset: int = 0,
) -> list[BookingRead]:
    rows = await crud_booking.list_open(db, limit=limit, offset=offset)
    return [_booking_read(b) for b in rows]


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    body: BookingCreate,
    db: AsyncSession = Depends(get_db),
    owner_id: UUID = Depends(get_current_user_id),
) -> BookingRead:
    dog = await crud_dog.get(db, body.dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_dog")

    walker = None
    price = Decimal("0.00")
    if body.walker_id is not None:
        walker = await crud_walker.get(db, body.walker_id)
        if not walker:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_walker")
        hours = Decimal(body.duration_minutes) / Decimal(60)
        price = (walker.price_per_hour * hours).quantize(Decimal("0.01"))

    booking = await crud_booking.create(
        db,
        {
            "owner_id": owner_id,
            "walker_id": walker.id if walker else None,
            "dog_id": body.dog_id,
            "scheduled_at": body.scheduled_at,
            "duration_minutes": body.duration_minutes,
            "price": price,
            "status": BookingStatus.PENDING,
            "address_country": body.address_country,
            "address_city": body.address_city,
            "address_street": body.address_street,
            "address_house": body.address_house,
            "address_apartment": body.address_apartment,
            "meeting_latitude": body.meeting_latitude,
            "meeting_longitude": body.meeting_longitude,
            "owner_notes": body.owner_notes,
        },
    )
    if walker:
        await send_notifications(
            [
                (
                    walker.user_id,
                    "Новая заявка на выгул",
                    "Поступило новое бронирование — подтвердите или отклоните в приложении.",
                    {"booking_id": str(booking.id), "event": "booking_pending"},
                ),
            ]
        )
    return _booking_read(booking)


@router.post("/{booking_id}/accept", response_model=BookingRead)
async def accept_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> BookingRead:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="deprecated_use_applications_choose",
    )


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> BookingRead:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if booking.walker_id is None:
        if booking.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return _booking_read(booking)
    walker = await crud_walker.get(db, booking.walker_id)
    if not walker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if booking.owner_id != user_id and walker.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return _booking_read(booking)


@router.patch("/{booking_id}/status", response_model=BookingRead)
async def update_booking_status(
    booking_id: UUID,
    body: BookingStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> BookingRead:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    walker = None
    if booking.walker_id is not None:
        walker = await crud_walker.get(db, booking.walker_id)
        if not walker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    is_owner = booking.owner_id == user_id
    is_walker = walker is not None and walker.user_id == user_id
    new_status = body.status

    allowed = False
    if booking.walker_id is None:
        if new_status == BookingStatus.CANCELLED and is_owner:
            allowed = booking.status == BookingStatus.PENDING
    elif new_status == BookingStatus.CONFIRMED and is_walker:
        allowed = booking.status == BookingStatus.PENDING
    elif new_status == BookingStatus.IN_PROGRESS and is_walker:
        allowed = booking.status == BookingStatus.CONFIRMED
    elif new_status == BookingStatus.COMPLETED and is_walker:
        allowed = booking.status == BookingStatus.IN_PROGRESS
    elif new_status == BookingStatus.CANCELLED and (is_owner or is_walker):
        allowed = booking.status in (
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
            BookingStatus.IN_PROGRESS,
        )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_transition",
        )

    data = {"status": new_status}
    if new_status == BookingStatus.CANCELLED:
        data["cancel_reason"] = body.cancel_reason

    updated = await crud_booking.update(db, booking, data)

    bid = str(booking.id)
    if new_status == BookingStatus.CONFIRMED:
        await send_notifications(
            [
                (
                    booking.owner_id,
                    "Бронирование подтверждено",
                    "Выгульщик подтвердил заказ.",
                    {"booking_id": bid, "event": "booking_confirmed"},
                ),
            ]
        )
        await schedule_walk_reminder(
            booking.owner_id,
            booking.id,
            booking.scheduled_at,
        )
    elif new_status == BookingStatus.IN_PROGRESS:
        await send_notifications(
            [
                (
                    booking.owner_id,
                    "Прогулка началась",
                    "Выгульщик начал прогулку — можно следить на карте.",
                    {"booking_id": bid, "event": "walk_started"},
                ),
            ]
        )
    elif new_status == BookingStatus.COMPLETED:
        await send_notifications(
            [
                (
                    booking.owner_id,
                    "Прогулка завершена",
                    "Оплатите услугу и при желании оставьте отзыв.",
                    {"booking_id": bid, "event": "walk_completed_owner"},
                ),
                (
                    walker.user_id,
                    "Прогулка завершена",
                    "Заказ отмечен как выполненный.",
                    {"booking_id": bid, "event": "walk_completed_walker"},
                ),
            ]
        )
    elif new_status == BookingStatus.CANCELLED:
        await cancel_scheduled_reminders(booking.id)
        reason = body.cancel_reason or "Без указания причины"
        if walker:
            other = booking.owner_id if is_walker else walker.user_id
            await send_notifications(
                [
                    (
                        other,
                        "Бронирование отменено",
                        reason,
                        {"booking_id": bid, "event": "booking_cancelled"},
                    ),
                ]
            )

    return _booking_read(updated)
