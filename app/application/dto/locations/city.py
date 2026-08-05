import re
from typing import Optional, Union
from fastapi import UploadFile
from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException
from app.utils.validation import has_excessive_repeating_chars

INVALID_CITY_NAME_PATTERN = re.compile(r"[<>\"`]")


@dataclass(config=ConfigDict(extra="forbid"))
class CityDTO:
    name: str
    country_id: str
    image_url: Optional[Union[str, UploadFile]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value or not value.strip():
            raise AppException(
                status_code=422,
                message="City name cannot be empty.",
                field="name",
                error_code="CITY_NAME_EMPTY",
            )

        cleaned = value.strip()
        if len(cleaned) > 50:
            raise AppException(
                status_code=422,
                message="City name must be 50 characters or fewer.",
                field="name",
                error_code="CITY_NAME_TOO_LONG",
            )

        if INVALID_CITY_NAME_PATTERN.search(cleaned):
            raise AppException(
                status_code=422,
                message="City name contains invalid characters.",
                field="name",
                error_code="CITY_NAME_INVALID",
            )

        if has_excessive_repeating_chars(cleaned):
            raise AppException(
                status_code=422,
                message="City name contains too many repeating characters.",
                field="name",
                error_code="CITY_NAME_REPETITIVE",
            )

        return cleaned


@dataclass(config=ConfigDict(extra="forbid"))
class CityFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class CityQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    country_id: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[CityFilterDTO]] = None