from typing import Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException


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
    room_type_id: Optional[int] = None
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
    vendor_id: str
    name: str
    location_id: str
    city_id: str
    is_featured: bool = False
    description: Optional[str] = None
    

   

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        from app.utils.validation import validate_name_field
        return validate_name_field(value, "name", 50, "PROPERTY_NAME")




@dataclass(config=ConfigDict(extra="forbid"))
class PropertyUpdateDTO:
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[str] = None
    city_id: Optional[str] = None
    room_type_id: Optional[str] = None
    main_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    max_guests: Optional[int] = None
    price_per_night: Optional[float] = None
    currency: Optional[str] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is None:
            return value
        from app.utils.validation import validate_name_field
        return validate_name_field(value, "name", 50, "PROPERTY_NAME")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value):
        if value is not None and not value.strip():
            raise AppException(
                status_code=422,
                message="Currency cannot be empty.",
                field="currency",
                error_code="CURRENCY_EMPTY",
            )
        return value.strip().upper() if value is not None else value

    @field_validator("max_guests")
    @classmethod
    def validate_max_guests(cls, value):
        if value is not None and value < 1:
            raise AppException(
                status_code=422,
                message="Max guests must be at least 1.",
                field="max_guests",
                error_code="MAX_GUESTS_INVALID",
            )
        return value

    @field_validator("price_per_night")
    @classmethod
    def validate_price(cls, value):
        if value is not None and value < 0:
            raise AppException(
                status_code=422,
                message="Price per night cannot be negative.",
                field="price_per_night",
                error_code="PRICE_INVALID",
            )
        return value
