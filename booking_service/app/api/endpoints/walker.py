import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.walker_crud import crud_walker
from app.schemas.walker import WalkerCreate, WalkerRead, WalkerUpdate

router = APIRouter(prefix="/walkers", tags=["walkers"])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p = math.pi / 180
    a = (
        0.5
        - math.cos((lat2 - lat1) * p) / 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    )
    return 2 * r * math.asin(math.sqrt(a))


@router.get("/search", response_model=list[WalkerRead])
async def search_walkers(
    db: AsyncSession = Depends(get_db),
    lat: float | None = Query(None),
    lng: float | None = Query(None),
    radius_km: float = Query(10.0, ge=0.5, le=100),
    min_rating: float | None = Query(None),
    max_price: float | None = Query(None),
    only_available: bool = True,
    limit: int = Query(20, le=100),
    offset: int = 0,
) -> list[WalkerRead]:
    walkers = await crud_walker.search(
        db,
        is_available=only_available,
        min_rating=min_rating,
        max_price=max_price,
        limit=200,
        offset=0,
    )
    if lat is None or lng is None:
        return [WalkerRead.model_validate(w) for w in walkers[:limit]]

    nearby: list[tuple[float, object]] = []
    for w in walkers:
        if w.latitude is None or w.longitude is None:
            continue
        dist = _haversine_km(lat, lng, w.latitude, w.longitude)
        max_r = min(radius_km, w.service_radius_km or radius_km)
        if dist <= max_r:
            nearby.append((dist, w))
    nearby.sort(key=lambda x: x[0])
    sliced = [w for _, w in nearby[offset : offset + limit]]
    return [WalkerRead.model_validate(w) for w in sliced]


@router.post("/me", response_model=WalkerRead, status_code=status.HTTP_201_CREATED)
async def create_my_walker_profile(
    body: WalkerCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalkerRead:
    existing = await crud_walker.get_by_user_id(db, user_id)
    if existing:
        raise HTTPException(status_code=409, detail="walker_profile_exists")
    data = body.model_dump()
    data["user_id"] = user_id
    if data.get("experience_years") is None:
        data["experience_years"] = 0
    obj = await crud_walker.create(db, data)
    return WalkerRead.model_validate(obj)


@router.get("/me", response_model=WalkerRead)
async def get_my_walker_profile(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalkerRead:
    w = await crud_walker.get_by_user_id(db, user_id)
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return WalkerRead.model_validate(w)


@router.patch("/me", response_model=WalkerRead)
async def update_my_walker_profile(
    body: WalkerUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalkerRead:
    w = await crud_walker.get_by_user_id(db, user_id)
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        return WalkerRead.model_validate(w)
    updated = await crud_walker.update(db, w, data)
    return WalkerRead.model_validate(updated)


@router.get("/{walker_id}", response_model=WalkerRead)
async def get_walker_by_id(
    walker_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> WalkerRead:
    w = await crud_walker.get(db, walker_id)
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return WalkerRead.model_validate(w)
