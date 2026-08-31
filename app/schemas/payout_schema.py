from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base_schema import BaseResponseSchema


class VendorBankAccountSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    account_type: str
    account_holder_name: str
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    upi_id: Optional[str] = None
    is_primary: bool
    is_verified: bool
    razorpay_contact_id: Optional[str] = None
    razorpay_fund_account_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PayoutVendorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None


class PayoutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    amount: float
    gross_amount: Optional[float] = None
    commission_amount: Optional[float] = None
    currency: str
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
    created_at: datetime
    updated_at: datetime

    vendor: Optional[PayoutVendorSchema] = None
    bank_account: Optional[VendorBankAccountSchema] = None


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


class PayoutResponseSchema(BaseResponseSchema):
    data: PayoutSchema


class PayoutListResponseSchema(BaseResponseSchema):
    data: List[PayoutSchema]


class VendorBankAccountResponseSchema(BaseResponseSchema):
    data: VendorBankAccountSchema


class VendorBankAccountListResponseSchema(BaseResponseSchema):
    data: List[VendorBankAccountSchema]


class VendorEarningsSummaryResponseSchema(BaseResponseSchema):
    data: VendorEarningsSummarySchema


class ProcessPayoutResponseSchema(BaseResponseSchema):
    data: PayoutSchema

