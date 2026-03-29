from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db_crud.user_crud import crud_user
from app.models.user import User
from app.schemas.user import UserRetrieveSchema, UpdateUserSchema

router = APIRouter(prefix="/user", tags=["users"])

@router.get('/me')
async def read_me(
    current_user: User = Depends(get_current_user)
) -> UserRetrieveSchema:
    return current_user


@router.patch("/me")
async def update_me(
    schema:UpdateUserSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserRetrieveSchema:
    data = schema.model_dump(exclude_unset=True, exclude_none=True)
    return await crud_user.update(db, current_user, data)


@router.delete('/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud_user.delete(db, current_user)