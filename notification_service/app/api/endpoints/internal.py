from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_internal
from app.db.session import get_db
from app.db_crud.notification_crud import crud_notification
from app.db_crud.scheduled_crud import crud_scheduled
from app.schemas.notification import (
    CancelByBookingBody,
    InternalNotifyBatch,
    InternalScheduleBatch,
)

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal)],
)


@router.post("/notifications", status_code=204)
async def enqueue_notifications(
    body: InternalNotifyBatch,
    db: AsyncSession = Depends(get_db),
) -> None:
    for item in body.items:
        await crud_notification.create(
            db,
            {
                "user_id": item.user_id,
                "title": item.title,
                "body": item.body,
                "data": item.data,
                "channel": "in_app",
            },
        )


@router.post("/scheduled-notifications", status_code=204)
async def schedule_notifications(
    body: InternalScheduleBatch,
    db: AsyncSession = Depends(get_db),
) -> None:
    for item in body.items:
        await crud_scheduled.create(
            db,
            {
                "user_id": item.user_id,
                "title": item.title,
                "body": item.body,
                "data": item.data,
                "fire_at": item.fire_at,
                "sent_at": None,
            },
        )


@router.post("/scheduled-notifications/cancel-by-booking", status_code=204)
async def cancel_scheduled_by_booking(
    body: CancelByBookingBody,
    db: AsyncSession = Depends(get_db),
) -> None:
    await crud_scheduled.cancel_for_booking(db, body.booking_id)
