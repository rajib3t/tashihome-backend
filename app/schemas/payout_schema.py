from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse, PaginationResponse


class VendorBankAccountSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    public_id: Optional[UUID] = None
    account_type: str
    account_holder_name: str
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    upi_id: Optional[str] = None
    is_primary: bool = True
    is_verified: bool = False
    razorpay_contact_id: Optional[str] = None
    razorpay_fund_account_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None


class PayoutVendorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    public_id: Optional[UUID] = None
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None


class PayoutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    public_id: Optional[UUID] = None
    amount: float
    gross_amount: Optional[float] = None
    commission_amount: Optional[float] = None
    currency: str = "INR"
    period_start: date
    period_end: date
    status: str
    mode: Optional[str] = None
    transaction_id: Optional[str] = None
    razorpay_payout_id: Optional[str] = None
    razorpay_fund_account_id: Optional[str] = None
    utr: Optional[str] = None
    failure_reason: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    vendor: Optional[PayoutVendorSchema] = None
    bank_account: Optional[VendorBankAccountSchema] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None

    @field_validator("amount", "gross_amount", "commission_amount", mode="before")
    @classmethod
    def validate_amounts(cls, value):
        return float(value) if value is not None else None


class VendorEarningsSummarySchema(BaseModel):
    vendor_public_id: UUID
    vendor_name: Optional[str] = None
    vendor_email: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    completed_bookings_count: int
    gross_booking_amount: float
    commission_percentage: float
    commission_amount: float
    net_earned_amount: float
    already_disbursed_amount: float
    pending_payable_amount: float

    @field_validator(
        "gross_booking_amount",
        "commission_percentage",
        "commission_amount",
        "net_earned_amount",
        "already_disbursed_amount",
        "pending_payable_amount",
        mode="before",
    )
    @classmethod
    def validate_floats(cls, value):
        return float(value) if value is not None else 0.0


class PayoutResponseSchema(BaseResponse):
    data: PayoutSchema


class PayoutListResponseSchema(PaginationResponse):
    data: List[PayoutSchema]


class VendorBankAccountResponseSchema(BaseResponse):
    data: VendorBankAccountSchema


class VendorBankAccountListResponseSchema(BaseResponse):
    data: List[VendorBankAccountSchema]


class VendorEarningsSummaryResponseSchema(BaseResponse):
    data: VendorEarningsSummarySchema


class ProcessPayoutResponseSchema(BaseResponse):
    data: PayoutSchema
