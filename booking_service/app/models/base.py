from contextlib import suppress
from datetime import datetime
from uuid import UUID as PY_UUID
from uuid import uuid4

from sqlalchemy import MetaData, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData()

    id: Mapped[PY_UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    extra_fields: Mapped[dict | None] = mapped_column(JSONB)

    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        symbols = [s if s.islower() else ("_" + s).lower() for s in cls.__name__]
        return "".join(symbols)[1:]

    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        db_obj_dict = self.__dict__.copy()
        del db_obj_dict["_sa_instance_state"]
        for exc in exclude or []:
            with suppress(KeyError):
                del db_obj_dict[exc]
        return db_obj_dict