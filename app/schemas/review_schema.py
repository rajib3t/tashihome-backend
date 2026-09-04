from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse, PaginationResponse


class ReviewGuestSchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_profile_image_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None


class ReviewPropertySchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: Optional[str] = None
    slug: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None


class ReviewBookingSchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    booking_reference: Optional[str] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None


class ReviewSchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    rating: int
    comment: Optional[str] = None
    host_reply: Optional[str] = None
    host_replied_at: Optional[datetime] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    guest: Optional[ReviewGuestSchema] = None
    property: Optional[ReviewPropertySchema] = None
    booking: Optional[ReviewBookingSchema] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value):
        return value.value if hasattr(value, "value") else str(value)


class ReviewResponseSchema(BaseResponse):
    data: ReviewSchema


class ReviewListResponseSchema(PaginationResponse):
    data: List[ReviewSchema]


class PropertyRatingSummarySchema(BaseModel):
    average_rating: float = 0.0
    total_reviews: int = 0
    rating_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    )
    model_config = ConfigDict(from_attributes=True)


class PropertyRatingSummaryResponseSchema(BaseResponse):
    data: PropertyRatingSummarySchema

