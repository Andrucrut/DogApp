from uuid import UUID

from app.schemas.base import BaseModel


class RoleRead(BaseModel):
    id: UUID
    name: str
    key: str
    description: str | None
    permissions: int


class RoleCreate(BaseModel):
    name: str
    key: str
    description: str | None = None
    permissions: int = 0


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: int | None = None