from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.property_asset_schema import PropertyAssetSchema
from app.schemas.response import BaseResponse, PaginationResponse


class BookingGuestSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class BookingPropertySchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: Optional[str] = None
    slug: Optional[str] = None
    address: Optional[str] = None
    price_per_night: Optional[float] = None
    sale_per_night: Optional[float] = None
    currency: Optional[str] = "INR"
    property_assets: Optional[List[PropertyAssetSchema]] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class BookingRoomTypeSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: Optional[str] = None
    capacity: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class BookingCancellationPolicySchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: Optional[str] = None
    description: Optional[str] = None
    refund_tiers: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class BookingPaymentSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    amount: float
    currency: str = "INR"
    payment_method: Optional[str] = None
    gateway: Optional[str] = None
    transaction_id: Optional[str] = None
    status: str
    refunded_amount: Optional[float] = 0.0
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)

    @field_validator("amount", "refunded_amount", mode="before")
    @classmethod
    def validate_floats(cls, value):
        if value is None:
            return 0.0
        return float(value)


class BookingRefundRequestSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    amount: float
    reason: Optional[str] = None
    status: str
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value):
        if value is None:
            return 0.0
        return float(value)


class BookingSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    booking_reference: str
    check_in_date: date
    check_out_date: date
    num_guests: int
    num_rooms: int
    price_per_night: float
    discount_amount: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    total_amount: float
    currency: str = "INR"
    status: str
    payment_status: str
    special_requests: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    guest: Optional[BookingGuestSchema] = None
    property: Optional[BookingPropertySchema] = None
    room_type: Optional[BookingRoomTypeSchema] = None
    cancellation_policy: Optional[BookingCancellationPolicySchema] = None
    payments: Optional[List[BookingPaymentSchema]] = None
    refund_requests: Optional[List[BookingRefundRequestSchema]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)

    @field_validator("price_per_night", "discount_amount", "tax_amount", "total_amount", mode="before")
    @classmethod
    def validate_numeric(cls, value):
        if value is None:
            return 0.0
        return float(value)


class BookingResponseSchema(BaseResponse):
    data: BookingSchema


class BookingListResponseSchema(PaginationResponse):
    data: List[BookingSchema]


class BookingQuoteSchema(BaseModel):
    nights: int
    num_rooms: int
    num_guests: int
    price_per_night: float
    base_amount: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    currency: str = "INR"
    model_config = ConfigDict(from_attributes=True)


class BookingQuoteResponseSchema(BaseResponse):
    data: BookingQuoteSchema


class BookingAvailabilityDataSchema(BaseModel):
    is_available: bool
    available_units: int
    total_units: int
    booked_units: int
    blocked_units: int
    requested_rooms: int
    quote: Optional[BookingQuoteSchema] = None
    model_config = ConfigDict(from_attributes=True)


class BookingAvailabilityResponseSchema(BaseResponse):
    data: BookingAvailabilityDataSchema


class BookingCancelResponseData(BaseModel):
    booking: BookingSchema
    refund_percentage: float
    refund_amount: float
    policy_summary: str
    refund_request_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class BookingCancelResponseSchema(BaseResponse):
    data: BookingCancelResponseData


class BookingPaymentResponseSchema(BaseResponse):
    data: BookingPaymentSchema


class BookingPaymentListResponseSchema(BaseResponse):
    data: List[BookingPaymentSchema]


class RazorpayOrderSchema(BaseModel):
    order_id: str
    amount: float
    amount_in_paise: int
    currency: str = "INR"
    key_id: str
    booking_id: str
    booking_reference: str
    model_config = ConfigDict(from_attributes=True)


class RazorpayOrderResponseSchema(BaseResponse):
    data: RazorpayOrderSchema

