from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_internal
from app.db.session import get_db
from app.models.user import User
from app.schemas.internal import (
    PublicProfilesRequest,
    PublicProfilesResponse,
    UserPublicProfileItem,
)

router = APIRouter(prefix="/internal", tags=["internal"])

_MAX_IDS = 50


@router.post("/users/public-profiles", response_model=PublicProfilesResponse)
async def post_public_profiles(
    body: PublicProfilesRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal),
) -> PublicProfilesResponse:
    deduped = list(dict.fromkeys(body.user_ids))[:_MAX_IDS]
    if not deduped:
        return PublicProfilesResponse(items=[])
    result = await db.execute(
        select(User).where(User.id.in_(deduped), User.deleted_at == None)
    )
    users = list(result.scalars().all())
    items = [
        UserPublicProfileItem(
            id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            avatar=u.avatar,
            city=u.city,
        )
        for u in users
    ]
    return PublicProfilesResponse(items=items)
