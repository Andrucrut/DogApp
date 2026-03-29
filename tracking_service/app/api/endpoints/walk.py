from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.track_point_crud import crud_track_point
from app.db_crud.walk_session_crud import crud_walk_session
from app.models.walk_session import WalkSessionStatus
from app.realtime.broadcast import walk_hub
from app.schemas.walk import (
    TrackPointIn,
    TrackPointRead,
    WalkSessionRead,
    WalkSessionStart,
)
from app.services.booking_client import fetch_booking_actors

router = APIRouter(prefix="/walk-sessions", tags=["walk-sessions"])

_ALLOWED_BOOKING_STATUS = frozenset({"CONFIRMED", "IN_PROGRESS"})


def _can_view_session(session, user_id: UUID) -> bool:
    return user_id in (session.owner_id, session.walker_user_id)


@router.post("/start", response_model=WalkSessionRead, status_code=status.HTTP_201_CREATED)
async def start_walk_session(
    body: WalkSessionStart,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalkSessionRead:
    info = await fetch_booking_actors(body.booking_id)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="booking_service_unavailable",
        )
    if not info.walker_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no_walker_assigned",
        )
    if user_id != info.walker_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if info.status not in _ALLOWED_BOOKING_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_booking_status",
        )

    existing = await crud_walk_session.get_live_for_booking(db, body.booking_id)
    if existing:
        return WalkSessionRead.model_validate(existing)

    now = datetime.now(timezone.utc)
    session = await crud_walk_session.create(
        db,
        {
            "booking_id": body.booking_id,
            "owner_id": info.owner_id,
            "walker_user_id": info.walker_user_id,
            "status": WalkSessionStatus.LIVE,
            "started_at": now,
            "ended_at": None,
        },
    )
    await walk_hub.publish_point(
        session.id,
        {"type": "session_started", "session_id": str(session.id), "at": now.isoformat()},
    )
    return WalkSessionRead.model_validate(session)


@router.get("/by-booking/{booking_id}", response_model=WalkSessionRead | None)
async def get_session_by_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalkSessionRead | None:
    session = await crud_walk_session.get_by_booking_id(db, booking_id)
    if not session:
        return None
    if not _can_view_session(session, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return WalkSessionRead.model_validate(session)


@router.get("/{session_id}", response_model=WalkSessionRead)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalkSessionRead:
    session = await crud_walk_session.get(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if not _can_view_session(session, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return WalkSessionRead.model_validate(session)


@router.get("/{session_id}/points", response_model=list[TrackPointRead])
async def list_points(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = 500,
) -> list[TrackPointRead]:
    session = await crud_walk_session.get(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if not _can_view_session(session, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    pts = await crud_track_point.list_for_session(db, session_id, limit=limit)
    return [TrackPointRead.model_validate(p) for p in pts]


@router.post("/{session_id}/points", response_model=TrackPointRead)
async def add_point(
    session_id: UUID,
    body: TrackPointIn,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> TrackPointRead:
    session = await crud_walk_session.get(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if session.walker_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if session.status != WalkSessionStatus.LIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_not_live")

    recorded_at = body.recorded_at or datetime.now(timezone.utc)
    point = await crud_track_point.create(
        db,
        {
            "session_id": session_id,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "accuracy_m": body.accuracy_m,
            "recorded_at": recorded_at,
        },
    )
    await walk_hub.publish_point(
        session_id,
        {
            "type": "point",
            "lat": point.latitude,
            "lng": point.longitude,
            "recorded_at": point.recorded_at.isoformat(),
        },
    )
    return TrackPointRead.model_validate(point)


@router.post("/{session_id}/finish", response_model=WalkSessionRead)
async def finish_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalkSessionRead:
    session = await crud_walk_session.get(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if session.walker_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if session.status != WalkSessionStatus.LIVE:
        return WalkSessionRead.model_validate(session)

    now = datetime.now(timezone.utc)
    updated = await crud_walk_session.update(
        db,
        session,
        {"status": WalkSessionStatus.COMPLETED, "ended_at": now},
    )
    await walk_hub.publish_point(
        session_id,
        {"type": "session_ended", "ended_at": now.isoformat()},
    )
    return WalkSessionRead.model_validate(updated)
