from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.application_crud import crud_booking_application
from app.db_crud.booking_crud import crud_booking
from app.db_crud.chat_crud import crud_conversation
from app.db_crud.walker_crud import crud_walker
from app.models.application import ApplicationStatus, BookingApplication
from app.models.booking import BookingStatus
from app.schemas.application import BookingApplicationRead, ChooseApplicationBody
from app.services.account_client import fetch_public_profiles
from app.services.outbound import send_notifications

router = APIRouter(prefix="/bookings/{booking_id}/applications", tags=["applications"])


def _avatar_from_profile(p: dict | None) -> UUID | None:
    if not p:
        return None
    v = p.get("avatar")
    if v is None:
        return None
    if isinstance(v, str):
        try:
            return UUID(v)
        except ValueError:
            return None
    return v if isinstance(v, UUID) else None


async def _to_application_reads(
    db: AsyncSession,
    apps: list[BookingApplication],
    *,
    conversation_id: UUID | None = None,
) -> list[BookingApplicationRead]:
    if not apps:
        return []
    wmap = await crud_walker.get_by_ids(db, [a.walker_id for a in apps])
    profiles = await fetch_public_profiles(list({a.walker_user_id for a in apps}))
    out: list[BookingApplicationRead] = []
    for a in apps:
        w = wmap.get(a.walker_id)
        p = profiles.get(a.walker_user_id)
        base = BookingApplicationRead.model_validate(a)
        out.append(
            base.model_copy(
                update={
                    "walker_first_name": (p or {}).get("first_name") if p else None,
                    "walker_last_name": (p or {}).get("last_name") if p else None,
                    "walker_avatar": _avatar_from_profile(p),
                    "walker_city": (p or {}).get("city") if p else None,
                    "walker_rating": float(w.rating) if w else None,
                    "walker_reviews_count": int(w.reviews_count) if w else None,
                    "walker_price_per_hour": w.price_per_hour if w else None,
                    "conversation_id": conversation_id,
                }
            )
        )
    return out


@router.post("/", response_model=BookingApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> BookingApplicationRead:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")
    if booking.walker_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already_assigned")

    walker = await crud_walker.get_by_user_id(db, user_id)
    if not walker:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not_a_walker")
    if booking.owner_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_apply_own_booking")

    existing = await crud_booking_application.get_for_booking_walker(db, booking_id, walker.id)
    if existing and existing.status not in (
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.REJECTED,
    ):
        reads = await _to_application_reads(db, [existing])
        return reads[0]

    if existing and existing.status in (
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.REJECTED,
    ):
        updated = await crud_booking_application.update(db, existing, {"status": ApplicationStatus.PENDING})
        await send_notifications(
            [
                (
                    booking.owner_id,
                    "Новый отклик на заявку",
                    "Выгульщик откликнулся на вашу заявку.",
                    {"booking_id": str(booking.id), "event": "booking_application_created"},
                ),
            ]
        )
        reads = await _to_application_reads(db, [updated])
        return reads[0]

    application = await crud_booking_application.create(
        db,
        {
            "booking_id": booking.id,
            "walker_id": walker.id,
            "walker_user_id": walker.user_id,
            "status": ApplicationStatus.PENDING,
        },
    )
    await send_notifications(
        [
            (
                booking.owner_id,
                "Новый отклик на заявку",
                "Выгульщик откликнулся на вашу заявку.",
                {"booking_id": str(booking.id), "event": "booking_application_created"},
            ),
        ]
    )
    reads = await _to_application_reads(db, [application])
    return reads[0]


@router.post("/withdraw", response_model=BookingApplicationRead)
async def withdraw_application(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> BookingApplicationRead:
    walker = await crud_walker.get_by_user_id(db, user_id)
    if not walker:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not_a_walker")
    app = await crud_booking_application.get_for_booking_walker(db, booking_id, walker.id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if app.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")
    updated = await crud_booking_application.update(db, app, {"status": ApplicationStatus.WITHDRAWN})
    reads = await _to_application_reads(db, [updated])
    return reads[0]


@router.get("/", response_model=list[BookingApplicationRead])
async def list_applications(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[BookingApplicationRead]:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if booking.owner_id == user_id:
        rows = await crud_booking_application.list_for_booking(db, booking_id, limit=limit, offset=offset)
        conv = await crud_conversation.get_by_booking_id(db, booking_id)
        conv_id = conv.id if conv else None
        return await _to_application_reads(db, rows, conversation_id=conv_id)
    walker = await crud_walker.get_by_user_id(db, user_id)
    if not walker:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    app = await crud_booking_application.get_for_booking_walker(db, booking_id, walker.id)
    if not app:
        return []
    return await _to_application_reads(db, [app])


@router.post("/choose", response_model=BookingApplicationRead)
async def choose_application(
    booking_id: UUID,
    body: ChooseApplicationBody,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> BookingApplicationRead:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if booking.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")

    rows = await crud_booking_application.list_for_booking(db, booking_id, limit=1000, offset=0)
    selected = next((r for r in rows if r.id == body.application_id), None)
    if not selected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if selected.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")

    walker = await crud_walker.get(db, selected.walker_id)
    if not walker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    hours = Decimal(booking.duration_minutes) / Decimal(60)
    price = (walker.price_per_hour * hours).quantize(Decimal("0.01"))
    await crud_booking.update(
        db,
        booking,
        {
            "walker_id": walker.id,
            "price": price,
            "status": BookingStatus.CONFIRMED,
        },
    )
    await crud_booking_application.set_status_for_booking(db, booking_id, accepted_walker_id=walker.id)

    conversation = await crud_conversation.get_by_booking_id(db, booking_id)
    if not conversation:
        conversation = await crud_conversation.create(
            db,
            {
                "booking_id": booking_id,
                "owner_id": booking.owner_id,
                "walker_user_id": walker.user_id,
            },
        )
    conv_id = conversation.id

    await send_notifications(
        [
            (
                booking.owner_id,
                "Выгульщик выбран",
                "Заявка подтверждена. Открылся чат с выбранным выгульщиком.",
                {"booking_id": str(booking_id), "event": "application_chosen_owner"},
            ),
            (
                walker.user_id,
                "Вас выбрали на заявку",
                "Владелец выбрал вас исполнителем. Чат открыт.",
                {"booking_id": str(booking_id), "event": "application_chosen_walker"},
            ),
        ]
    )
    refreshed = await crud_booking_application.get(db, selected.id)
    reads = await _to_application_reads(db, [refreshed], conversation_id=conv_id)
    return reads[0]


@router.post("/{application_id}/reject", response_model=BookingApplicationRead)
async def reject_application(
    booking_id: UUID,
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> BookingApplicationRead:
    booking = await crud_booking.get(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if booking.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    app_row = await crud_booking_application.get(db, application_id)
    if not app_row or app_row.booking_id != booking_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if app_row.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")

    updated = await crud_booking_application.update(
        db, app_row, {"status": ApplicationStatus.REJECTED}
    )
    reads = await _to_application_reads(db, [updated])
    return reads[0]
