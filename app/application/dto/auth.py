import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from app.core.exceptions import AppException
from pydantic.dataclasses import dataclass
from app.utils.validation import validate_name_field
# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------
def normalize_email(value: str) -> str:
    return value.strip().lower()


class AuthDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str
    rememberMe: Optional[bool] = False

    @field_validator("email", mode="before")
    @classmethod
    def email_validator(cls, value: str):
        if isinstance(value, str):
            return normalize_email(value)
        return value


class RegisterDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    full_name: str
    password: str
    phone: Optional[str] = None
    is_subscriber: bool = False
    is_terms_accept: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def email_validator(cls, value: str):
        if isinstance(value, str):
            return normalize_email(value)
        return value
    
    @field_validator("full_name", mode="before")
    @classmethod
    def full_name_validator(cls, value: str):
        if isinstance(value, str):
            return validate_name_field(value, field_name="full_name", max_length=50, error_code_prefix="FULL_NAME")
        return value
    
    @field_validator("password", mode="before")
    @classmethod
    def password_validator(cls, value: str):
        if isinstance(value, str):
            if not value or not value.strip():
                raise AppException(
                    status_code=422,
                    message="Password cannot be empty.",
                    field="password",
                    error_code="PASSWORD_EMPTY",
                )
            if len(value.strip()) < 8:
                raise AppException(
                    status_code=422,
                    message="Password must be at least 8 characters long.",
                    field="password",
                    error_code="PASSWORD_TOO_SHORT",
                )
            return value.strip()
        return value
    
    
    @field_validator("phone", mode="before")
    @classmethod
    def phone_validator(cls, value: Optional[str]):
        if value is None:
            return value
        if isinstance(value, str):
            phone = value.strip()
            # Enforce stricter phone format: E.164-like (optional +, 8-15 digits)
            if phone and not re.match(r'^\+?\d{8,15}$', phone):
                raise AppException(
                    status_code=422,
                    message="Phone number must be 8-15 digits, optionally starting with '+'.",
                    field="phone",
                    error_code="PHONE_INVALID",
                )
            return phone if phone else None
        return value
    
    @field_validator("is_subscriber", mode="before")
    @classmethod
    def is_subscriber_validator(cls, value: bool):
        if isinstance(value, bool):
            return value
        return value
    
    @field_validator("is_terms_accept", mode="before")
    @classmethod
    def is_terms_accept_validator(cls, value: bool):
        if isinstance(value, bool):
            if not value:
                raise AppException(
                    status_code=422,
                    message="You must accept the terms and conditions.",
                    field="is_terms_accept",
                    error_code="TERMS_NOT_ACCEPTED",
                )
            return value
        return value
    
   
    

class ForgotPasswordDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def email_validator(cls, value):
        if not isinstance(value, str):
            raise AppException(
                status_code=422,
                message="Email must be a string.",
                field="email",
                error_code="EMAIL_INVALID",
            )

        email = value.strip().lower()

        if not email:
            raise AppException(
                status_code=422,
                message="Email cannot be empty.",
                field="email",
                error_code="EMAIL_EMPTY",
            )

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise AppException(
                status_code=422,
                message="Invalid email format.",
                field="email",
                error_code="EMAIL_INVALID",
            )

        return email


class ResetPasswordDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    password: str
    confirm_password: str

    @field_validator("token", mode="before")
    @classmethod
    def token_validator(cls, value: str):
        if not isinstance(value, str):
            raise AppException(
                status_code=422,
                message="Token must be a string.",
                field="token",
                error_code="TOKEN_INVALID",
            )
        if not value.strip():
            raise AppException(
                status_code=422,
                message="Token cannot be empty.",
                field="token",
                error_code="TOKEN_EMPTY",
            )
        return value.strip()
    
    @field_validator("password", mode="before")
    @classmethod
    def password_validator(cls, value: str):
        if not isinstance(value, str):
            raise AppException(
                status_code=422,
                message="Password must be a string.",
                field="password",
                error_code="PASSWORD_INVALID",
            )
        if not value.strip():
            raise AppException(
                status_code=422,
                message="Password cannot be empty.",
                field="password",
                error_code="PASSWORD_EMPTY",
            )
        if len(value.strip()) < 8:
            raise AppException(
                status_code=422,
                message="Password must be at least 8 characters long.",
                field="password",
                error_code="PASSWORD_TOO_SHORT",
            )
        return value.strip()
    
    @field_validator("confirm_password", mode="before")
    @classmethod
    def confirm_password_validator(cls, value: str):
        if not isinstance(value, str):
            raise AppException(
                status_code=422,
                message="Confirm password must be a string.",
                field="confirm_password",
                error_code="CONFIRM_PASSWORD_INVALID",
            )
        if not value.strip():
            raise AppException(
                status_code=422,
                message="Confirm password cannot be empty.",
                field="confirm_password",
                error_code="CONFIRM_PASSWORD_EMPTY",
            )
        return value.strip()
    
    @model_validator(mode="after")
    def check_passwords_match(self) -> "ResetPasswordDTO":
        if self.password != self.confirm_password:
            raise AppException(
                status_code=422,
                message="Passwords do not match.",
                field="confirm_password",
                error_code="PASSWORDS_MISMATCH",
            )
        return self