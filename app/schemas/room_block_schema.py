from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse, PaginationResponse


class RoomBlockPropertySchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: Optional[str] = None
    slug: Optional[str] = None
    address: Optional[str] = None
    price_per_night: Optional[float] = None
    currency: Optional[str] = "INR"

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)

    @field_validator("price_per_night", mode="before")
    @classmethod
    def validate_price(cls, value):
        if value is None:
            return None
        return float(value)


class RoomBlockRoomTypeSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: Optional[str] = None
    capacity: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class RoomBlockCreatorSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class RoomBlockSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    block_start_date: date
    block_end_date: date
    units_blocked: int
    reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    property: Optional[RoomBlockPropertySchema] = None
    room_type: Optional[RoomBlockRoomTypeSchema] = None
    creator: Optional[RoomBlockCreatorSchema] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class RoomBlockResponseSchema(BaseResponse):
    data: RoomBlockSchema


class RoomBlockListResponseSchema(PaginationResponse):
    data: List[RoomBlockSchema]

