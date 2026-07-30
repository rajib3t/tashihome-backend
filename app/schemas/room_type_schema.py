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
