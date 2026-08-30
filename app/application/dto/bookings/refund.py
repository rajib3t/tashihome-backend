from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic.dataclasses import dataclass
from pydantic import ConfigDict

from app.core.exceptions import AppException


@dataclass(config=ConfigDict(extra="forbid"))
class AdminRefundQueryDTO:
    """Query params for listing refund requests."""
    page: int = 1
    size: int = 10
    status: Optional[str] = None
    booking_id: Optional[str] = None
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

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]):
        if value is None:
            return None
        allowed = ["pending", "approved", "rejected", "processed"]
        if value.strip().lower() not in allowed:
            raise AppException(
                status_code=422,
                message=f"Invalid status '{value}'. Allowed: {', '.join(allowed)}",
                field="status",
                error_code="INVALID_STATUS",
            )
        return value.strip().lower()


class AdminRefundStatusUpdateDTO(BaseModel):
    """Request body for admin approve/reject refund."""
    status: str
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        allowed = ["approved", "rejected"]
        if value.strip().lower() not in allowed:
            raise AppException(
                status_code=422,
                message=f"Invalid status '{value}'. Allowed: {', '.join(allowed)}",
                field="status",
                error_code="INVALID_STATUS",
            )
        return value.strip().lower()

