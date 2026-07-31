from typing import Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException


@dataclass(config=ConfigDict(extra="forbid"))
class RoomTypeDTO:
    name: str
    capacity: int


@dataclass(config=ConfigDict(extra="forbid"))
class RoomTypeFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class RoomTypeQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[RoomTypeFilterDTO]] = None

    @field_validator("page", "size")
    def validate_positive(cls, value):
        if value < 1:
            raise AppException(
                status_code=422,
                message="Size must be between 1 and 100.",
                field="size",
                error_code="SIZE_INVALID",
            )

        return value

    @field_validator("sort_order")
    def validate_sort_order(cls, value):
        if value not in ["asc", "desc"]:
            raise AppException(
                status_code=422,
                message="Sort order must be 'asc' or 'desc'.",
                field="sort_order",
                error_code="SORT_ORDER_INVALID",
            )
        return value
