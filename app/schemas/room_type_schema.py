from typing import Optional
from pydantic import AliasChoices, BaseModel, Field, field_validator
from sqlalchemy import UUID

from app.schemas.response import BaseResponse, PaginationResponse


class RoomTypeBase(BaseModel):
    name: str
    capacity: int
    status: str


class RoomTypeSchema(RoomTypeBase):
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    is_global: bool = True
    vendor_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("vendor_public_id", "vendor_id"),
        serialization_alias="vendor_id",
    )

    @field_validator("vendor_id", mode="before")
    @classmethod
    def validate_vendor_id(cls, value):
        if value is None:
            return None
        return str(value)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class RoomTypeResponseSchema(BaseResponse):
    data: RoomTypeSchema


class RoomTypeListResponseSchema(PaginationResponse):
    data: list[RoomTypeSchema]


RoomTypeSchema.model_rebuild()
RoomTypeResponseSchema.model_rebuild()
RoomTypeListResponseSchema.model_rebuild()
