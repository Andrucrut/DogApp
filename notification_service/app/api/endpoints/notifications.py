from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.notification_crud import crud_notification
from app.schemas.notification import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationRead])
async def list_my_notifications(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
) -> list[NotificationRead]:
    rows = await crud_notification.list_for_user(
        db,
        user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )
    return [NotificationRead.model_validate(r) for r in rows]


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> NotificationRead:
    from datetime import datetime, timezone

    n = await crud_notification.get(db, notification_id)
    if not n or n.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    updated = await crud_notification.update(
        db,
        n,
        {"read_at": datetime.now(timezone.utc)},
    )
    return NotificationRead.model_validate(updated)
