from pydantic import AliasChoices, BaseModel, Field, field_validator
from sqlalchemy import UUID

from app.schemas.response import BaseResponse, PaginationResponse


class PropertyBase(BaseModel):
    vendor_id: int
    location_id: int | None = None
    city_id: int | None = None
    room_type_id: int | None = None
    name: str
    slug: str
    description: str | None = None
    main_image_url: str | None = None
    cover_image_url: str | None = None
    max_guests: int = 1
    price_per_night: float = 0.0
    currency: str = "INR"
    is_featured: bool = False
    status: str


class PropertySchema(PropertyBase):
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


class PropertyResponseSchema(BaseResponse):
    data: PropertySchema


class PropertyListResponseSchema(PaginationResponse):
    data: list[PropertySchema]
