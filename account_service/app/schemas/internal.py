from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseModel


class UserPublicProfileItem(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    avatar: UUID | None
    city: str | None


class PublicProfilesRequest(BaseModel):
    user_ids: list[UUID] = Field(default_factory=list, max_length=50)


class PublicProfilesResponse(BaseModel):
    items: list[UserPublicProfileItem]
