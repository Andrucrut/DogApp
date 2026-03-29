from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.schedule_crud import crud_schedule
from app.db_crud.walker_crud import crud_walker
from app.schemas.schedule import ScheduleCreate, ScheduleRead, ScheduleUpdate

router = APIRouter(prefix="/schedules", tags=["schedules"])


async def _walker_for_user(db: AsyncSession, user_id: UUID):
    walker = await crud_walker.get_by_user_id(db, user_id)
    if not walker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="walker_profile_not_found",
        )
    return walker


@router.get("/me", response_model=list[ScheduleRead])
async def list_my_schedule(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[ScheduleRead]:
    walker = await crud_walker.get_by_user_id(db, user_id)
    if not walker:
        return []
    rows = await crud_schedule.list_by_walker(db, walker.id)
    return [ScheduleRead.model_validate(s) for s in rows]


@router.post("/me", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
async def add_slot(
    body: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> ScheduleRead:
    walker = await _walker_for_user(db, user_id)
    if not (0 <= body.day_of_week <= 6):
        raise HTTPException(status_code=400, detail="invalid_day_of_week")
    obj = await crud_schedule.create(
        db,
        {
            "walker_id": walker.id,
            "day_of_week": body.day_of_week,
            "time_from": body.time_from,
            "time_to": body.time_to,
            "is_active": True,
        },
    )
    return ScheduleRead.model_validate(obj)


@router.patch("/{schedule_id}", response_model=ScheduleRead)
async def update_slot(
    schedule_id: UUID,
    body: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> ScheduleRead:
    walker = await _walker_for_user(db, user_id)
    slot = await crud_schedule.get(db, schedule_id)
    if not slot or slot.walker_id != walker.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        return ScheduleRead.model_validate(slot)
    updated = await crud_schedule.update(db, slot, data)
    return ScheduleRead.model_validate(updated)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> None:
    walker = await _walker_for_user(db, user_id)
    slot = await crud_schedule.get(db, schedule_id)
    if not slot or slot.walker_id != walker.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await crud_schedule.soft_delete(db, slot)
