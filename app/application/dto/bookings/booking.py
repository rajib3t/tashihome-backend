from datetime import date
from typing import Optional

from pydantic import AliasChoices, ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException


@dataclass(config=ConfigDict(extra="forbid"))
class BookingCreateDTO:
    property_id: str
    check_in_date: date
    check_out_date: date
    room_type_id: Optional[str] = None
    num_guests: int = 1
    num_rooms: int = 1
    special_requests: Optional[str] = None

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

    @field_validator("num_guests", "num_rooms")
    @classmethod
    def validate_positive_counts(cls, value: int, info):
        if value is None or value < 1:
            raise AppException(
                status_code=422,
                message=f"{info.field_name} must be at least 1.",
                field=info.field_name,
                error_code="INVALID_COUNT",
            )
        return value

    @field_validator("special_requests")
    @classmethod
    def validate_special_requests(cls, value: Optional[str]):
        if value is None:
            return None
        trimmed = value.strip()
        if len(trimmed) > 1000:
            raise AppException(
                status_code=422,
                message="Special requests cannot exceed 1000 characters.",
                field="special_requests",
                error_code="TEXT_TOO_LONG",
            )
        return trimmed or None


@dataclass(config=ConfigDict(extra="forbid"))
class BookingQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    status: Optional[str] = None
    payment_status: Optional[str] = None
    search: Optional[str] = None

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
        allowed = ["created_at", "check_in_date", "check_out_date", "total_amount", "status"]
        if value not in allowed:
            return "created_at"
        return value


@dataclass(config=ConfigDict(extra="ignore"))
class BookingCancelDTO:
    reason: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("reason", "cancellation_reason"),
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: Optional[str]):
        if value is None:
            return None
        trimmed = str(value).strip()
        if len(trimmed) > 255:
            raise AppException(
                status_code=422,
                message="Cancellation reason cannot exceed 255 characters.",
                field="reason",
                error_code="TEXT_TOO_LONG",
            )
        return trimmed or None

    @property
    def cancellation_reason(self) -> Optional[str]:
        return self.reason


@dataclass(config=ConfigDict(extra="forbid"))
class BookingPaymentDTO:
    payment_method: str
    amount: Optional[float] = None
    transaction_id: Optional[str] = None
    gateway: Optional[str] = "internal"

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value: str):
        allowed = ["card", "upi", "netbanking", "wallet", "cash", "bank_transfer"]
        normalized = str(value).strip().lower()
        if normalized not in allowed:
            raise AppException(
                status_code=422,
                message=f"Invalid payment method '{value}'. Allowed: {', '.join(allowed)}",
                field="payment_method",
                error_code="INVALID_PAYMENT_METHOD",
            )
        return normalized

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Optional[float]):
        if value is not None and value <= 0:
            raise AppException(
                status_code=422,
                message="Payment amount must be greater than 0.",
                field="amount",
                error_code="INVALID_AMOUNT",
            )
        return value


@dataclass(config=ConfigDict(extra="forbid"))
class BookingAvailabilityDTO:
    property_id: str
    check_in_date: date
    check_out_date: date
    room_type_id: Optional[str] = None
    num_rooms: int = 1
    num_guests: int = 1

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

    @field_validator("num_rooms", "num_guests")
    @classmethod
    def validate_counts(cls, value: int, info):
        if value is None or value < 1:
            raise AppException(
                status_code=422,
                message=f"{info.field_name} must be at least 1.",
                field=info.field_name,
                error_code="INVALID_COUNT",
            )
        return value


@dataclass(config=ConfigDict(extra="forbid"))
class RazorpayCreateOrderDTO:
    amount: Optional[float] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Optional[float]):
        if value is not None and value <= 0:
            raise AppException(
                status_code=422,
                message="Amount must be greater than 0.",
                field="amount",
                error_code="INVALID_AMOUNT",
            )
        return value


@dataclass(config=ConfigDict(extra="forbid"))
class RazorpayVerifyPaymentDTO:
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

    @field_validator("razorpay_order_id", "razorpay_payment_id", "razorpay_signature")
    @classmethod
    def validate_non_empty(cls, value: str, info):
        if not value or not str(value).strip():
            raise AppException(
                status_code=422,
                message=f"{info.field_name} is required.",
                field=info.field_name,
                error_code="FIELD_REQUIRED",
            )
        return str(value).strip()


@dataclass(config=ConfigDict(extra="forbid"))
class AdminBookingQueryDTO:
    """Query params for admin listing all bookings."""
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    status: Optional[str] = None
    payment_status: Optional[str] = None
    search: Optional[str] = None
    property_id: Optional[str] = None
    guest_id: Optional[str] = None
    check_in_date: Optional[date] = None
    check_in_from: Optional[date] = None
    check_in_to: Optional[date] = None

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
        allowed = ["created_at", "check_in_date", "check_out_date", "total_amount", "status"]
        if value not in allowed:
            return "created_at"
        return value


from pydantic import BaseModel


class BookingStatusUpdateDTO(BaseModel):
    """Request body for admin/vendor status update."""
    status: str
    reason: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        from app.models.booking_model import BookingStatus
        allowed = [s.value for s in BookingStatus]
        if value not in allowed:
            raise AppException(
                status_code=422,
                message=f"Invalid status '{value}'. Allowed: {', '.join(allowed)}",
                field="status",
                error_code="INVALID_STATUS",
            )
        return value
