from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.models.host_request_model import HostRequestStatus
from app.schemas.response import BaseResponse, PaginationResponse


class HostRequestMessageResponseData(BaseModel):
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    sender_id: Optional[str] = None
    sender_name: str
    sender_role: str
    message: str
    is_internal: bool = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class HostRequestResponseData(BaseModel):
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    user_id: Optional[str] = None
    full_name: str
    email: str
    phone: str
    company_name: Optional[str] = None
    property_name: Optional[str] = None
    property_type: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    expected_rooms: Optional[int] = None
    notes: Optional[str] = None
    status: HostRequestStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    converted_user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: Optional[list[HostRequestMessageResponseData]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class HostRequestSingleResponseSchema(BaseResponse):
    data: HostRequestResponseData


class HostRequestListResponseSchema(PaginationResponse):
    data: list[HostRequestResponseData]

