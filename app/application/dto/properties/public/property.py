from app.core.exceptions import AppException
from pydantic import field_validator
from typing_extensions import Optional
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyFilterDTO:
    name: str
    value: str

@dataclass(config=ConfigDict(extra="forbid"))
class PublicPropertyQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    city_slug: Optional[str] = None
    location_slug: Optional[str] = None
    country_slug: Optional[str] = None
    city_id: Optional[str] = None
    location_id: Optional[str] = None
    country_id: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_featured: Optional[bool] = None
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

    @field_validator("size")
    @classmethod
    def validate_max_size(cls, value):
        if value > 100:
            raise AppException(
                status_code=422,
                message="Size must be 100 or less.",
                field="size",
                error_code="PAGINATION_INVALID",
            )
        return value

    @field_validator("min_price", "max_price")
    @classmethod
    def validate_prices(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise AppException(
                status_code=422,
                message="Price cannot be negative.",
                field="price",
                error_code="INVALID_PRICE",
            )
        return value

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value: str) -> str:
        if value.lower() not in ["asc", "desc"]:
            raise AppException(
                status_code=422,
                message="Sort order must be 'asc' or 'desc'.",
                field="sort_order",
                error_code="SORT_ORDER_INVALID",
            )
        return value.lower()

    @field_validator("sort_by", "sortBy")
    @classmethod
    def validate_sort_by(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        allowed = ["created_at", "name", "price", "price_asc", "price_desc", "price_low_to_high", "price_high_to_low"]
        if value.lower() not in allowed:
            raise AppException(
                status_code=422,
                message=f"Sort by must be one of: {', '.join(allowed)}.",
                field="sort_by",
                error_code="INVALID_SORT_BY",
            )
        return value.lower()

    @field_validator("is_featured", mode="before")
    @classmethod
    def validate_is_featured(cls, value):
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "yes", "t")
        return bool(value)

    def __post_init__(self):
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise AppException(
                    status_code=422,
                    message="min_price cannot be greater than max_price.",
                    field="min_price",
                    error_code="INVALID_PRICE_RANGE",
                )