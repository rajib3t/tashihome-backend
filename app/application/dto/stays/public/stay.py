from datetime import date
from typing import Optional, List
from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass
from app.core.exceptions import AppException


@dataclass(config=ConfigDict(extra="forbid"))
class PublicSearchStaysQueryDTO:
    # Text / Region / Location search
    region: Optional[str] = None
    search: Optional[str] = None
    q: Optional[str] = None
    
    # Location by name (preferred) or ID
    city_name: Optional[str] = None
    city: Optional[str] = None
    location_name: Optional[str] = None
    location: Optional[str] = None
    country_name: Optional[str] = None
    country: Optional[str] = None
    
    city_id: Optional[str] = None
    location_id: Optional[str] = None
    country_id: Optional[str] = None

    # Dates
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None

    # Guests and Rooms
    guests: Optional[int] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    rooms: Optional[int] = 1

    # Pricing
    min_price: Optional[float] = None
    max_price: Optional[float] = None

    # Attributes & Types
    type: Optional[str] = None
    amenity_ids: Optional[List[str]] = None
    facility_ids: Optional[List[str]] = None
    is_featured: Optional[bool] = None

    # Pagination & Sorting
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    size: int = 10

    @field_validator("page", "size")
    @classmethod
    def validate_positive_pagination(cls, value: int) -> int:
        if value < 1:
            raise AppException(
                status_code=422,
                message="Page and size must be greater than 0.",
                field="page",
                error_code="PAGINATION_INVALID",
            )
        return value

    @field_validator("guests", "adults", "children", "rooms")
    @classmethod
    def validate_positive_counts(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 0:
            raise AppException(
                status_code=422,
                message="Guest and room counts cannot be negative.",
                error_code="INVALID_COUNT",
            )
        return value

    @field_validator("min_price", "max_price")
    @classmethod
    def validate_prices(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise AppException(
                status_code=422,
                message="Price cannot be negative.",
                error_code="INVALID_PRICE",
            )
        return value

