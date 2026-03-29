from datetime import date, datetime
from typing import Literal
from typing import Self
from uuid import UUID

from pydantic import EmailStr, field_validator, model_validator

from app.models.base import UserStatus
from app.schemas.base import BaseModel
from app.schemas.role import RoleRead


class CreateUserSchema(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    telegram: str | None = None
    first_name: str
    last_name: str
    middle_name: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    country: str | None = None
    city: str | None = None
    consent_personal_data: bool
    consent_privacy_policy: bool
    password: str
    role_key: Literal["owner", "walker"] = "owner"

    @field_validator("consent_personal_data", "consent_privacy_policy")
    @classmethod
    def must_be_true(cls, v: bool, info) -> bool:
        if not v:
            raise ValueError(f"{info.field_name} must be accepted")
        return v

    @model_validator(mode="after")
    def email_or_phone_required(self) -> Self:
        if not self.email and not self.phone:
            raise ValueError("Email или телефон обязателен")
        return self

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        password = value.strip()
        if len(password) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Пароль слишком длинный: максимум 72 байта")
        return password


class UpdateUserSchema(BaseModel):
    avatar: UUID | None = None
    telegram: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    country: str | None = None
    city: str | None = None


class UserRetrieveSchema(BaseModel):
    id: UUID
    email: str | None = None
    phone: str | None = None
    telegram: str | None = None
    first_name: str
    last_name: str
    middle_name: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    country: str | None = None
    city: str | None = None
    avatar: UUID | None = None
    status: UserStatus
    is_active: bool
    is_superuser: bool
    is_verified: bool
    role_id: UUID
    role: RoleRead
    created_at: datetime
    deleted_at: datetime | None = None