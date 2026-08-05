from typing import Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException


@dataclass(config=ConfigDict(extra="forbid"))
class CountryFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class CountryQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[CountryFilterDTO]] = None

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


@dataclass(config=ConfigDict(extra="forbid"))
class CountryDTO:
    name: str
    code: str
    

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        from app.utils.validation import validate_name_field
        return validate_name_field(value, "name", 50, "COUNTRY_NAME")

    @field_validator("code")
    @classmethod
    def validate_code(cls, value):
        if not value or not value.strip():
            raise AppException(
                status_code=422,
                message="Code cannot be empty.",
                field="code",
                error_code="CODE_EMPTY",
            )
        return value.strip()


    
