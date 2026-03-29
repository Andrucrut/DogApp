from typing import Self
from uuid import UUID

from pydantic import EmailStr, field_validator, model_validator
from exceptions import ErrorCodes
from app.schemas.base import BaseModel


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    password: str

    @model_validator(mode="after")
    def email_or_phone_required(self) -> Self:
        if not self.email and not self.phone:
            raise ValueError(ErrorCodes.EMAIL_OR_PHONE_REQUIRED)
        return self

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Пароль слишком длинный: максимум 72 байта")
        return value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenUserDataSchema(BaseModel):
    user_id: UUID
    role: str
    permissions: int
    email: str


