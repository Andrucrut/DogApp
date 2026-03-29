from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.review_crud import crud_review
from app.schemas.review import ReviewCreate, ReviewRead
from app.services.booking_client import apply_walker_rating, fetch_review_context

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> ReviewRead:
    ctx = await fetch_review_context(body.booking_id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="booking_unavailable",
        )
    if ctx.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if not ctx.eligible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="booking_not_eligible",
        )
    if not ctx.walker_profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no_walker_assigned",
        )

    dup = await crud_review.get_by_booking_id(db, body.booking_id)
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already_reviewed")

    review = await crud_review.create(
        db,
        {
            "booking_id": body.booking_id,
            "reviewer_owner_id": user_id,
            "walker_profile_id": ctx.walker_profile_id,
            "rating": body.rating,
            "comment": body.comment,
        },
    )

    applied = await apply_walker_rating(ctx.walker_profile_id, body.rating)
    if not applied:
        await crud_review.soft_delete(db, review)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="rating_update_failed",
        )

    return ReviewRead.model_validate(review)


@router.get("/me", response_model=list[ReviewRead])
async def list_my_reviews(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = 50,
    offset: int = 0,
) -> list[ReviewRead]:
    rows = await crud_review.list_by_reviewer(db, user_id, limit=limit, offset=offset)
    return [ReviewRead.model_validate(r) for r in rows]


@router.get("/walkers/{walker_profile_id}", response_model=list[ReviewRead])
async def list_walker_reviews(
    walker_profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> list[ReviewRead]:
    rows = await crud_review.list_for_walker(
        db,
        walker_profile_id,
        limit=limit,
        offset=offset,
    )
    return [ReviewRead.model_validate(r) for r in rows]
