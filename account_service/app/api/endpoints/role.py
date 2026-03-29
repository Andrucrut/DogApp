from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser
from app.db.session import get_db
from app.db_crud.role_crud import crud_role
from app.models.user import User
from app.schemas.role import RoleRead, RoleCreate, RoleUpdate

router = APIRouter(prefix="/role", tags=["Role"])


@router.get("/")
async def get_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[RoleRead]:
    return await crud_role.get_all(db)


@router.get('/{role_id}')
async def get_role_by_id(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> RoleRead:
    role = await crud_role.get(db, id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_role(
    schema:RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser)
) -> RoleRead:
    existing = await crud_role.get_by_key(db, key=schema.key)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="role_key_already_exists")
    return await crud_role.create(db, schema.model_dump())


@router.patch('/{role_id}')
async def update_role(
    role_id: UUID,
    schema: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> RoleRead:
    role = await crud_role.get(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role_not_found")
    return await crud_role.update(db, role, schema.model_dump(exclude_unset=True, exclude_none=True))


@router.delete('/{role_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser)
):
    role = await crud_role.get(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role_not_found")
    return await crud_role.soft_delete(db, role)