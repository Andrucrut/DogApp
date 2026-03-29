from typing import Self
import re

from pydantic import field_validator, model_validator, EmailStr
from exceptions import ErrorCodes
from app.schemas.base import BaseModel
PASSWORD_PATTERN = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[\d\W]).{8,}$"

class PasswordBaseSchema(BaseModel):
    password: str
    re_password: str

    @field_validator("password")
    @classmethod
    def validate(cls, v: str) -> str:
        if not re.match(PASSWORD_PATTERN, v):
            raise ValueError(ErrorCodes.WEAK_PASSWORD)
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.re_password:
            raise ValueError(ErrorCodes.PASSWORDS_MISMATCH)
        return self


class ChangePasswordSchema(PasswordBaseSchema):
    old_password: str


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(PasswordBaseSchema):
    token: str
