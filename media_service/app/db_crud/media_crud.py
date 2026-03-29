from app.db_crud.base import CRUDBase
from app.models.media_asset import MediaAsset


class CRUDMedia(CRUDBase[MediaAsset]):
    pass


crud_media = CRUDMedia(MediaAsset)
