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
    city_id: Optional[str] = None
    location_id: Optional[str] = None
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