from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.core.geo import is_spb_point
from app.db.session import get_db
from app.db_crud.track_point_crud import crud_track_point
from app.db_crud.walk_session_crud import crud_walk_session
from app.models.walk_session import WalkSessionStatus
from app.realtime.broadcast import walk_hub
from app.schemas.walk import (
    TrackPointPage,
    TrackPointIn,
    TrackPointRead,
    WalkRouteResponse,
    WalkRouteSummary,
    WalkSessionRead,
    WalkSessionStart,
)
from app.services.booking_client import fetch_booking_actors

router = APIRouter(prefix="/walk-sessions", tags=["walk-sessions"])

_ALLOWED_BOOKING_STATUS = frozenset({"CONFIRMED", "IN_PROGRESS"})


def _norm_booking_status(raw: object) -> str:
    """Enum/строка из booking internal API → верхний регистр без префикса."""
    s = str(raw).strip()
    if "." in s:
        s = s.rsplit(".", 1)[-1]
    return s.upper()


def _can_view_session(session, user_id: UUID) -> bool:
    return user_id in (session.owner_id, session.walker_user_id)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


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
    if _norm_booking_status(info.status) not in _ALLOWED_BOOKING_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_booking_status",
        )

    existing = await crud_walk_session.get_live_for_booking(db, body.booking_id)
    if existing:
        return WalkSessionRead.model_validate(existing)

    tomb = await crud_walk_session.get_by_booking_id_any(db, body.booking_id)
    if tomb:
        if tomb.deleted_at is not None:
            await crud_walk_session.hard_delete_with_points(db, tomb)
        elif tomb.status != WalkSessionStatus.LIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="walk_session_finished",
            )
        else:
            # Гонка: другой запрос уже создал LIVE-сессию между get_live и этим чтением.
            return WalkSessionRead.model_validate(tomb)

    now = datetime.now(timezone.utc)
    try:
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
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="walk_session_conflict",
        ) from None
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


@router.get("/by-booking/{booking_id}/route", response_model=WalkRouteResponse | None)
async def get_route_by_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(10000, ge=1, le=20000),
    offset: int = Query(0, ge=0),
) -> WalkRouteResponse | None:
    session = await crud_walk_session.get_by_booking_id(db, booking_id)
    if not session:
        return None
    if not _can_view_session(session, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return await _build_route_response(db, session, limit=limit, offset=offset)


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


@router.get("/{session_id}/points", response_model=TrackPointPage)
async def list_points(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(2000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
) -> TrackPointPage:
    session = await crud_walk_session.get(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if not _can_view_session(session, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    pts = await crud_track_point.list_for_session(
        db, session_id, limit=limit, offset=offset
    )
    total = await crud_track_point.count_for_session(db, session_id)
    returned = len(pts)
    has_more = (offset + returned) < total
    return TrackPointPage(
        items=[TrackPointRead.model_validate(p) for p in pts],
        total=total,
        offset=offset,
        limit=limit,
        has_more=has_more,
    )


@router.get("/{session_id}/route", response_model=WalkRouteResponse)
async def get_route(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(10000, ge=1, le=20000),
    offset: int = Query(0, ge=0),
) -> WalkRouteResponse:
    session = await crud_walk_session.get(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if not _can_view_session(session, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return await _build_route_response(db, session, limit=limit, offset=offset)


async def _build_route_response(
    db: AsyncSession,
    session,
    *,
    limit: int,
    offset: int,
) -> WalkRouteResponse:
    points = await crud_track_point.list_for_session(
        db, session.id, limit=limit, offset=offset
    )
    total_points = await crud_track_point.count_for_session(db, session.id)
    returned_points = len(points)
    has_more = (offset + returned_points) < total_points
    total = 0.0
    min_lat = max_lat = min_lon = max_lon = None
    prev = None
    for p in points:
        if min_lat is None:
            min_lat = max_lat = p.latitude
            min_lon = max_lon = p.longitude
        else:
            min_lat = min(min_lat, p.latitude)
            max_lat = max(max_lat, p.latitude)
            min_lon = min(min_lon, p.longitude)
            max_lon = max(max_lon, p.longitude)
        if prev is not None:
            total += _haversine_m(prev.latitude, prev.longitude, p.latitude, p.longitude)
        prev = p

    duration_seconds = None
    started_at = points[0].recorded_at if points else session.started_at
    ended_at = points[-1].recorded_at if points else session.ended_at
    if started_at and ended_at:
        duration_seconds = max(0, int((ended_at - started_at).total_seconds()))

    return WalkRouteResponse(
        session=WalkSessionRead.model_validate(session),
        points=[TrackPointRead.model_validate(p) for p in points],
        summary=WalkRouteSummary(
            points_count=total_points,
            total_points=total_points,
            returned_points=returned_points,
            offset=offset,
            limit=limit,
            has_more=has_more,
            total_distance_m=round(total, 2),
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            min_latitude=min_lat,
            max_latitude=max_lat,
            min_longitude=min_lon,
            max_longitude=max_lon,
        ),
    )


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
    if not is_spb_point(body.latitude, body.longitude):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="point_outside_supported_city",
        )

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
