from app.schemas.response import PaginationResponse
from app.schemas.response import BaseResponse
from app.schemas.property_schema import PropertyCitySchema
from app.schemas.property_schema import PropertyLocationSchema

from typing import Optional

from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

class PropertyAssetSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    file_url: str | None = None

class PropertyVendorSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: str | None = None
    email: str | None = None
    is_profile_image_url : Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)
class PublicPropertyBase(BaseModel):
    
    name: str
    slug: str
    
    location: Optional[PropertyLocationSchema] = None
    city: Optional[PropertyCitySchema] = None
    type: Optional[str] = None
    price_per_night: Optional[float] = None
    sale_per_night: Optional[float] = None
    address: Optional[str] = None
    feature_image: Optional[PropertyAssetSchema] = None

class PropertyRoomTypeSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    room_type: Optional["RoomTypeNestedSchema"] = None
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
    amenity: Optional["AmenityNestedSchema"] = None
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
    facility: Optional["FacilityNestedSchema"] = None
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


class RoomTypeNestedSchema(BaseModel):
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


class AmenityNestedSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str | None = None
    icon_url: str | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class FacilityNestedSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str | None = None
    icon_url: str | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)

class PublicPropertyDetailResponse(PublicPropertyBase):
    id : UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str
    slug: str
    vendor: Optional[dict] = None
    location: Optional[PropertyLocationSchema] = None
    city: Optional[PropertyCitySchema] = None
    room_type: Optional[PropertyRoomTypeSchema] = None
    currency: Optional[str] = None
    type: Optional[str] = None
    price_per_night: Optional[float] = None
    sale_per_night: Optional[float] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    property_room_types: Optional[list[PropertyRoomTypeSchema]] = None
    property_amenities: Optional[list[PropertyAmenitySchema]] = None
    property_facilities: Optional[list[PropertyFacilitySchema]] = None
    property_food_options: Optional[list[PropertyFoodOptionSchema]] = None
    property_assets: Optional[list[PropertyAssetSchema]] = None
    gallery_images: Optional[list[PropertyAssetSchema]] = None
    feature_image: Optional[PropertyAssetSchema] = None
    cover_image: Optional[PropertyAssetSchema] = None

    status: str
    is_featured: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class PublicPropertySchema(PublicPropertyBase):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )

class PublicPropertyResponse(BaseResponse):
    data: PublicPropertyDetailResponse


class PublicPropertyResponseListSchema(PaginationResponse):
    data: list[PublicPropertySchema]

