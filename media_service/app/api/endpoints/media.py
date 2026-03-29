from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.db.session import get_db
from app.db_crud.media_crud import crud_media
from app.schemas.media import MediaRead

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> MediaRead:
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="too_large")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    asset_id = uuid4()
    storage_key = str(asset_id)
    path: Path = settings.UPLOAD_DIR / storage_key
    path.write_bytes(data)

    asset = await crud_media.create(
        db,
        {
            "id": asset_id,
            "owner_user_id": user_id,
            "content_type": file.content_type or "application/octet-stream",
            "size_bytes": len(data),
            "original_filename": file.filename,
            "storage_key": storage_key,
        },
    )
    return MediaRead.model_validate(asset)


@router.get("/{media_id}/file")
async def download_file(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    asset = await crud_media.get(db, media_id)
    if not asset or asset.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    path = settings.UPLOAD_DIR / asset.storage_key
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file_missing")
    return FileResponse(
        path,
        media_type=asset.content_type,
        filename=asset.original_filename or asset.storage_key,
    )


@router.get("/{media_id}", response_model=MediaRead)
async def get_meta(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    asset = await crud_media.get(db, media_id)
    if not asset or asset.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return MediaRead.model_validate(asset)
