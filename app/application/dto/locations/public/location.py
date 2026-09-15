from app.core.exceptions import AppException
from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass
from typing_extensions import Optional


@dataclass(config=ConfigDict(extra="ignore"))
class LocationFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="ignore"))
class PublicLocationQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: Optional[str] = "created_at"
    sortBy: Optional[str] = None
    sort_order: Optional[str] = "desc"
    sortOrder: Optional[str] = None
    name: Optional[str] = None
    city_id: Optional[str] = None
    search: Optional[str] = None
    filters: Optional[list[LocationFilterDTO]] = None

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

    @field_validator("sort_by", "sortBy")
    @classmethod
    def validate_sort_by(cls, value):
        if value is None:
            return None
        if value.lower() not in ["name", "created_at", "updated_at"]:
            raise AppException(
                status_code=422,
                message="Sort by must be one of: name, created_at, updated_at.",
                field="sort_by",
                error_code="SORT_INVALID",
            )
        return value.lower()

    @field_validator("sort_order", "sortOrder")
    @classmethod
    def validate_sort_order(cls, value):
        if value is None:
            return None
        if value.lower() not in ["asc", "desc"]:
            raise AppException(
                status_code=422,
                message="Sort order must be asc or desc.",
                field="sort_order",
                error_code="SORT_INVALID",
            )
        return value.lower()

    @field_validator("name", "search", "city_id")
    @classmethod
    def validate_text(cls, value):
        if value is not None:
            value = value.strip()
            if not value:
                return None
        return value
