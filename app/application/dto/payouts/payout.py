from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException


@dataclass(config=ConfigDict(extra="forbid"))
class AdminPayoutQueryDTO:
    """Query params for listing vendor payouts."""
    page: int = 1
    size: int = 10
    vendor_id: Optional[str] = None
    status: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
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
        allowed = ["pending", "processing", "paid", "failed", "reversed", "rejected", "cancelled"]
        if value.strip().lower() not in allowed:
            raise AppException(
                status_code=422,
                message=f"Invalid status '{value}'. Allowed: {', '.join(allowed)}",
                field="status",
                error_code="INVALID_STATUS",
            )
        return value.strip().lower()


@dataclass(config=ConfigDict(extra="forbid"))
class CalculateVendorEarningsDTO:
    """Query parameters for calculating eligible vendor dues."""
    vendor_id: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    commission_percentage: Optional[float] = None


class AdminPayoutCreateDTO(BaseModel):
    """Request body for creating a payout record."""
    vendor_id: str
    bank_account_id: Optional[str] = None
    gross_amount: Optional[float] = None
    commission_amount: Optional[float] = 0.0
    amount: float
    currency: Optional[str] = "INR"
    period_start: date
    period_end: date
    mode: Optional[str] = "NEFT"
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float):
        if value <= 0:
            raise AppException(
                status_code=422,
                message="Payout amount must be greater than 0.",
                field="amount",
                error_code="INVALID_AMOUNT",
            )
        return value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: Optional[str]):
        if not value:
            return "NEFT"
        allowed = ["NEFT", "RTGS", "IMPS", "UPI"]
        if value.upper() not in allowed:
            raise AppException(
                status_code=422,
                message=f"Invalid mode '{value}'. Allowed: {', '.join(allowed)}",
                field="mode",
                error_code="INVALID_MODE",
            )
        return value.upper()


class AdminPayoutProcessDTO(BaseModel):
    """Request body for processing a payout via RazorpayX."""
    mode: Optional[str] = None  # Override mode if needed (NEFT, IMPS, RTGS, UPI)
    narration: Optional[str] = "Vendor Payout"
    notes: Optional[dict] = None


class VendorBankAccountCreateDTO(BaseModel):
    """Request body for adding bank account for a vendor."""
    account_type: str = "bank_account"  # "bank_account" or "vpa"
    account_holder_name: str
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    upi_id: Optional[str] = None
    is_primary: bool = True
    notes: Optional[str] = None

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, value: str):
        allowed = ["bank_account", "vpa"]
        if value.lower() not in allowed:
            raise AppException(
                status_code=422,
                message=f"Invalid account_type '{value}'. Allowed: {', '.join(allowed)}",
                field="account_type",
                error_code="INVALID_ACCOUNT_TYPE",
            )
        return value.lower()


class VendorBankAccountUpdateDTO(BaseModel):
    """Request body for updating vendor bank account."""
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    upi_id: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None

