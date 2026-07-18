import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from app.core.exceptions import AppException
from pydantic.dataclasses import dataclass
# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------
def normalize_email(value: str) -> str:
    return value.strip().lower()


class AuthDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def email_validator(cls, value: str):
        if isinstance(value, str):
            return normalize_email(value)
        return value
