from typing import Optional

from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse, PaginationResponse


class PropertyVendorSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: str | None = None
    email: str | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class PropertyCitySchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class PropertyLocationSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class PropertyRoomTypeSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str | None = None
    capacity: int | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)

class PropertyAmenitySchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class PropertyFacilitySchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)
class PropertyFoodOptionSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str | None = None
    is_included: bool | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)
class PropertyBase(BaseModel):
    name: str
    slug: str
    vendor: Optional[PropertyVendorSchema] = None
    location: Optional[PropertyLocationSchema] = None
    city: Optional[PropertyCitySchema] = None
    room_type: Optional[PropertyRoomTypeSchema] = None
    currency: Optional[str] = None
    type: Optional[str] = None
    price_per_night: Optional[float] = None
    sale_per_night: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    amenities: Optional[list[PropertyAmenitySchema]] = None
    facilities: Optional[list[PropertyFacilitySchema]] = None
    food_options: Optional[list[PropertyFoodOptionSchema]] = None

    status: str
    model_config = ConfigDict(from_attributes=True)


class PropertySchema(PropertyBase):
    id: UUID | str | None = Field(
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
    model_config = ConfigDict(from_attributes=True)


class PropertyResponseSchema(BaseResponse):
    data: PropertySchema


class PropertyListResponseSchema(PaginationResponse):
    data: list[PropertySchema]
