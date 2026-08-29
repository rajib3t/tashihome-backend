from fastapi import UploadFile
from typing import List, Optional

from pydantic import AliasChoices, ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException
from app.utils.validation import validate_description


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    slug: Optional[str] = None
    vendor_id: Optional[int] = None
    location_id: Optional[int] = None
    city_id: Optional[int] = None
    status: Optional[str] = None
    filters: Optional[list[PropertyFilterDTO]] = None

    @field_validator("page", "size")
    @classmethod
    def validate_positive(cls, value):
        if value < 1:
            raise AppException(
                status_code=422,
                message="Page and size must be greater than 0.",
                field="page",
                error_code="PAGINATION_INVALID",
            )
        return value

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value):
        if value not in ["asc", "desc"]:
            raise AppException(
                status_code=422,
                message="Sort order must be 'asc' or 'desc'.",
                field="sort_order",
                error_code="SORT_ORDER_INVALID",
            )
        return value


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyDTO:
    name: str
    vendor: Optional[str] = None
    type: Optional[str] = None
    slug: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = Field(default=None, validation_alias=AliasChoices("latitude", "lat"))
    longitude: Optional[float] = Field(default=None, validation_alias=AliasChoices("longitude", "lon"))
    main_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    max_guests: Optional[int] = None
    vendor_id: Optional[str] = None
    location_id: Optional[str] = None
    city_id: Optional[str] = None
    room_type_id: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    price_per_night: Optional[float] = None
    sale_price: Optional[float] = None
    sale_per_night: Optional[float] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = None
    amenity_ids: Optional[List[str]] = None
    facility_ids: Optional[List[str]] = None
    room_type_ids: Optional[List[str]] = None
    food_option_ids: Optional[List[str]] = None
    amenities: Optional[List["PropertyAmenitiesDTO"]] = None
    facility: Optional[List["PropertyFacilityDTO"]] = None
    facilities: Optional[List["PropertyFacilityDTO"]] = None
    room_types: Optional[List["PropertyRoomTypeDTO"]] = None
    food_options: Optional[List["FoodOptionDTO"]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        from app.utils.validation import validate_name_field
        return validate_name_field(value, "name", 50, "PROPERTY_NAME")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        if value is None:
            return value
        from app.utils.validation import validate_description
        return validate_description(value, required=False, max_length=100)

    @field_validator("vendor", "type", "city", "location", "address")
    @classmethod
    def validate_text_fields(cls, value):
        if value is None:
            return value
        value = value.strip()
        return value or None

    @field_validator("slug")
    @classmethod
    def validate_slug_field(cls, value):
        if value is None:
            return value
        value = value.strip()
        return value or None


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyAmenitiesDTO:
    id: str


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyFacilityDTO:
    id: str


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyRoomTypeDTO:
    id: Optional[str] = None
    room_type_id: Optional[str] = None
    total_units: Optional[int] = 1


@dataclass(config=ConfigDict(extra="forbid"))
class FoodOptionDTO:
    name: str
    allow: bool = True


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyUpdateDTO(PropertyDTO):
    name: Optional[str] = None
    vendor: Optional[str] = None
    type: Optional[str] = None
    slug: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = Field(default=None, validation_alias=AliasChoices("latitude", "lat"))
    longitude: Optional[float] = Field(default=None, validation_alias=AliasChoices("longitude", "lon"))
    main_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    max_guests: Optional[int] = None
    vendor_id: Optional[str] = None
    location_id: Optional[str] = None
    city_id: Optional[str] = None
    room_type_id: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    price_per_night: Optional[float] = None
    sale_price: Optional[float] = None
    sale_per_night: Optional[float] = None
    currency: Optional[str] = None
    amenities: Optional[List[PropertyAmenitiesDTO]] = None
    facility: Optional[List[PropertyFacilityDTO]] = None
    facilities: Optional[List[PropertyFacilityDTO]] = None
    room_types: Optional[List[PropertyRoomTypeDTO]] = None
    food_options: Optional[List[FoodOptionDTO]] = None
    status: Optional[str] = None

    
@dataclass(config=ConfigDict(extra="forbid"))
class AssetsDTO:
    name: str 
    file: Optional[UploadFile] = None


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyAssetsDTO:
    gallery_images: Optional[List[AssetsDTO]] = None
    feature_image: Optional[AssetsDTO] = None
    cover_image: Optional[AssetsDTO] = None