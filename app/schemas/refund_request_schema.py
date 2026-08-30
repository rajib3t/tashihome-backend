from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse, PaginationResponse


class RefundRequestUserSchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: Optional[str] = None
    email: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None


class RefundRequestBookingSchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    booking_reference: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None


class RefundRequestPaymentSchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    amount: Optional[float] = None
    currency: Optional[str] = "INR"
    gateway: Optional[str] = None
    transaction_id: Optional[str] = None
    status: Optional[str] = None
    refunded_amount: Optional[float] = 0.0
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None

    @field_validator("amount", "refunded_amount", mode="before")
    @classmethod
    def validate_numeric(cls, value):
        return float(value) if value is not None else 0.0


class RefundRequestSchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    amount: float
    reason: Optional[str] = None
    status: str
    razorpay_refund_id: Optional[str] = None
    razorpay_status: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    booking: Optional[RefundRequestBookingSchema] = None
    payment: Optional[RefundRequestPaymentSchema] = None
    requester: Optional[RefundRequestUserSchema] = None
    approver: Optional[RefundRequestUserSchema] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value):
        return float(value) if value is not None else 0.0


class RefundRequestResponseSchema(BaseResponse):
    data: RefundRequestSchema


class RefundRequestListResponseSchema(PaginationResponse):
    data: List[RefundRequestSchema]


class ProcessRefundResponseData(BaseModel):
    refund_request: RefundRequestSchema
    razorpay_refund_id: Optional[str] = None
    razorpay_status: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ProcessRefundResponseSchema(BaseResponse):
    data: ProcessRefundResponseData

