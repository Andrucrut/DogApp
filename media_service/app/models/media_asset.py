from uuid import UUID as PY_UUID

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MediaAsset(Base):
    owner_user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(512))
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
