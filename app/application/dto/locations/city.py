from app.utils.validation import validate_description
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
    short_description : Optional[str]=None
    tag_line : Optional[str]=None
    is_featured: Optional[bool] = False
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
    @field_validator("short_description")
    @classmethod
    def validate_short_description(cls, value):
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if len(value) > 200:
            raise AppException(
                status_code=422,
                message="Short description must be 200 characters or fewer.",
                field="short_description",
                error_code="SHORT_DESCRIPTION_TOO_LONG",
            )
        if has_excessive_repeating_chars(value):
            raise AppException(
                status_code=422,
                message="Short description contains too many repeating characters.",
                field="short_description",
                error_code="SHORT_DESCRIPTION_REPETITIVE",
            )
        return validate_description(
            value,
            required=False,
            max_length=200,
            field_name="short_description",
            error_code_prefix="SHORT_DESCRIPTION",
        )

    @field_validator("tag_line")
    @classmethod
    def validate_tag_line(cls, value):
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if len(value) > 75:
            raise AppException(
                status_code=422,
                message="Tag line must be 75 characters or fewer.",
                field="tag_line",
                error_code="TAG_LINE_TOO_LONG",
            )
        if has_excessive_repeating_chars(value):
            raise AppException(
                status_code=422,
                message="Tag line contains too many repeating characters.",
                field="tag_line",
                error_code="TAG_LINE_REPETITIVE",
            )
        return validate_description(
            value,
            required=False,
            max_length=75,
            field_name="tag_line",
            error_code_prefix="TAG_LINE",
        )

    @field_validator("is_featured", mode="before")
    @classmethod
    def validate_is_featured(cls, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "yes", "t")
        return bool(value)



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