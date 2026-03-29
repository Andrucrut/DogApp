from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.db_crud.dog_crud import crud_dog
from app.schemas.dog import DogCreate, DogRead, DogUpdate

router = APIRouter(prefix="/dogs", tags=["dogs"])


@router.get("/", response_model=list[DogRead])
async def list_my_dogs(
    db: AsyncSession = Depends(get_db),
    owner_id: UUID = Depends(get_current_user_id),
) -> list[DogRead]:
    dogs = await crud_dog.list_by_owner(db, owner_id)
    return [DogRead.model_validate(d) for d in dogs]


@router.post("/", response_model=DogRead, status_code=status.HTTP_201_CREATED)
async def create_dog(
    body: DogCreate,
    db: AsyncSession = Depends(get_db),
    owner_id: UUID = Depends(get_current_user_id),
) -> DogRead:
    obj = await crud_dog.create(db, {**body.model_dump(), "owner_id": owner_id})
    return DogRead.model_validate(obj)


@router.get("/{dog_id}", response_model=DogRead)
async def get_dog(
    dog_id: UUID,
    db: AsyncSession = Depends(get_db),
    owner_id: UUID = Depends(get_current_user_id),
) -> DogRead:
    dog = await crud_dog.get(db, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return DogRead.model_validate(dog)


@router.patch("/{dog_id}", response_model=DogRead)
async def update_dog(
    dog_id: UUID,
    body: DogUpdate,
    db: AsyncSession = Depends(get_db),
    owner_id: UUID = Depends(get_current_user_id),
) -> DogRead:
    dog = await crud_dog.get(db, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        return DogRead.model_validate(dog)
    updated = await crud_dog.update(db, dog, data)
    return DogRead.model_validate(updated)


@router.delete("/{dog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dog(
    dog_id: UUID,
    db: AsyncSession = Depends(get_db),
    owner_id: UUID = Depends(get_current_user_id),
) -> None:
    dog = await crud_dog.get(db, dog_id)
    if not dog or dog.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await crud_dog.soft_delete(db, dog)
