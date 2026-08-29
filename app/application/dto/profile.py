import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.exceptions import AppException
from app.utils.validation import validate_name_field


class UpdateProfileInfoDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_subscribed: Optional[bool] = None

    @field_validator("full_name", mode="before")
    @classmethod
    def full_name_validator(cls, value: Optional[str]):
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise AppException(
                    status_code=422,
                    message="Full name cannot be empty.",
                    field="full_name",
                    error_code="FULL_NAME_EMPTY",
                )
            return validate_name_field(
                stripped,
                field_name="full_name",
                max_length=50,
                error_code_prefix="FULL_NAME",
            )
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def phone_validator(cls, value: Optional[str]):
        if value is None:
            return None
        if isinstance(value, str):
            phone = value.strip()
            if not phone:
                return None
            if not re.match(r"^\+?[\d\s\-()]{7,20}$", phone):
                raise AppException(
                    status_code=422,
                    message="Phone number format is invalid.",
                    field="phone",
                    error_code="PHONE_INVALID",
                )
            return phone
        return value

    @field_validator("is_subscribed", mode="before")
    @classmethod
    def is_subscribed_validator(cls, value: Optional[bool]):
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "yes", "t")
        return bool(value)


class UpdatePasswordDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("current_password", mode="before")
    @classmethod
    def current_password_validator(cls, value: str):
        if not isinstance(value, str) or not value.strip():
            raise AppException(
                status_code=422,
                message="Current password cannot be empty.",
                field="current_password",
                error_code="CURRENT_PASSWORD_EMPTY",
            )
        return value

    @field_validator("new_password", mode="before")
    @classmethod
    def new_password_validator(cls, value: str):
        if not isinstance(value, str) or not value.strip():
            raise AppException(
                status_code=422,
                message="New password cannot be empty.",
                field="new_password",
                error_code="NEW_PASSWORD_EMPTY",
            )
        stripped = value.strip()
        if len(stripped) < 8:
            raise AppException(
                status_code=422,
                message="New password must be at least 8 characters long.",
                field="new_password",
                error_code="PASSWORD_TOO_SHORT",
            )
        return stripped

    @field_validator("confirm_password", mode="before")
    @classmethod
    def confirm_password_validator(cls, value: str):
        if not isinstance(value, str) or not value.strip():
            raise AppException(
                status_code=422,
                message="Confirm password cannot be empty.",
                field="confirm_password",
                error_code="CONFIRM_PASSWORD_EMPTY",
            )
        return value.strip()

    @model_validator(mode="after")
    def validate_passwords(self) -> "UpdatePasswordDTO":
        if self.new_password != self.confirm_password:
            raise AppException(
                status_code=422,
                message="New password and confirm password do not match.",
                field="confirm_password",
                error_code="PASSWORDS_MISMATCH",
            )
        if self.current_password == self.new_password:
            raise AppException(
                status_code=422,
                message="New password must be different from current password.",
                field="new_password",
                error_code="PASSWORD_SAME_AS_CURRENT",
            )
        return self

