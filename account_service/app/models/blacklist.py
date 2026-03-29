from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text
from app.models.base import Base


class BlacklistToken(Base):
    __tablename__ = "blacklist_token"

    token: Mapped[str] = mapped_column(Text, unique=True, index=True)

    def __str__(self):
        return f"BlacklistToken ({self.id})"