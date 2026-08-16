from app.core.exceptions import AppException
from pydantic import field_validator
from typing_extensions import Optional
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class CityFilterDTO:
    name: str
    value: str

@dataclass(config=ConfigDict(extra="forbid"))
class PublicCityQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    country_id: Optional[str] = None
    is_featured: Optional[bool] = None
    filters: Optional[list[CityFilterDTO]] = None
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
    def validate_size(cls, value):
        if value > 100:
            raise AppException(
                status_code=422,
                message="Size must be less than or equal to 100.",
                field="size",
                error_code="PAGINATION_INVALID",
            )
        return value
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value):
        if value not in ["name", "created_at", "updated_at"]:
            raise AppException(
                status_code=422,
                message="Sort by must be one of: name, created_at, updated_at.",
                field="sort_by",
                error_code="SORT_INVALID",
            )
        return value
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value):
        if value not in ["asc", "desc"]:
            raise AppException(
                status_code=422,
                message="Sort order must be asc or desc.",
                field="sort_order",
                error_code="SORT_INVALID",
            )
        return value
    @field_validator("is_featured", mode='before')
    @classmethod
    def validate_is_featured(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip().lower() in ("true", "1", "yes", "t")
        return bool(value)