from datetime import date
from typing import Optional
from pydantic import ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException


@dataclass(config=ConfigDict(extra="forbid"))
class RoomBlockCreateDTO:
    property_id: str
    room_type_id: str
    block_start_date: date
    block_end_date: date
    units_blocked: int = 1
    reason: Optional[str] = None

    @field_validator("property_id")
    @classmethod
    def validate_property_id(cls, value: str):
        if not value or not str(value).strip():
            raise AppException(
                status_code=422,
                message="Property ID is required.",
                field="property_id",
                error_code="FIELD_REQUIRED",
            )
        return str(value).strip()

    @field_validator("room_type_id")
    @classmethod
    def validate_room_type_id(cls, value: str):
        if not value or not str(value).strip():
            raise AppException(
                status_code=422,
                message="Room Type ID is required.",
                field="room_type_id",
                error_code="FIELD_REQUIRED",
            )
        return str(value).strip()

    @field_validator("units_blocked")
    @classmethod
    def validate_units_blocked(cls, value: int):
        if value is None or value < 1:
            raise AppException(
                status_code=422,
                message="Units blocked must be at least 1.",
                field="units_blocked",
                error_code="INVALID_UNIT_COUNT",
            )
        return value

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: Optional[str]):
        if value is None:
            return None
        trimmed = str(value).strip()
        if len(trimmed) > 255:
            raise AppException(
                status_code=422,
                message="Reason cannot exceed 255 characters.",
                field="reason",
                error_code="TEXT_TOO_LONG",
            )
        return trimmed or None


@dataclass(config=ConfigDict(extra="forbid"))
class RoomBlockUpdateDTO:
    block_start_date: Optional[date] = None
    block_end_date: Optional[date] = None
    units_blocked: Optional[int] = None
    reason: Optional[str] = None

    @field_validator("units_blocked")
    @classmethod
    def validate_units_blocked(cls, value: Optional[int]):
        if value is not None and value < 1:
            raise AppException(
                status_code=422,
                message="Units blocked must be at least 1.",
                field="units_blocked",
                error_code="INVALID_UNIT_COUNT",
            )
        return value

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: Optional[str]):
        if value is None:
            return None
        trimmed = str(value).strip()
        if len(trimmed) > 255:
            raise AppException(
                status_code=422,
                message="Reason cannot exceed 255 characters.",
                field="reason",
                error_code="TEXT_TOO_LONG",
            )
        return trimmed or None


@dataclass(config=ConfigDict(extra="forbid"))
class RoomBlockQueryDTO:
    page: int = 1
    size: int = 10
    property_id: Optional[str] = None
    room_type_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"

    @field_validator("page", "size")
    @classmethod
    def validate_pagination(cls, value: int, info):
        if value < 1:
            raise AppException(
                status_code=422,
                message=f"{info.field_name} must be greater than 0.",
                field=info.field_name,
                error_code="PAGINATION_INVALID",
            )
        return value

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value: str):
        if value not in ["asc", "desc"]:
            raise AppException(
                status_code=422,
                message="Sort order must be 'asc' or 'desc'.",
                field="sort_order",
                error_code="SORT_ORDER_INVALID",
            )
        return value

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: str):
        allowed = ["created_at", "block_start_date", "block_end_date", "units_blocked", "updated_at"]
        if value not in allowed:
            return "created_at"
        return value

