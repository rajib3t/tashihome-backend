from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.models.user_model import UserRole
from app.schemas.response import BaseResponse


class VendorAddressData(BaseModel):
    id: str | None = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VendorCompanyData(BaseModel):
    id: str | None = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[VendorAddressData] = None

    model_config = ConfigDict(from_attributes=True)


class VendorUserData(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    status: str
    role: UserRole
    is_profile_image_url: str | None = None
    company: Optional[VendorCompanyData] = None

    model_config = ConfigDict(from_attributes=True)


class VendorUserResponseData(VendorUserData):
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class VendorResponseSchema(BaseResponse):
    data: VendorUserResponseData
