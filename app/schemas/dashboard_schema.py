from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse


class BookingStatsSchema(BaseModel):
    total: int = 0
    pending: int = 0
    confirmed: int = 0
    checked_in: int = 0
    checked_out: int = 0
    cancelled: int = 0
    completed: int = 0
    no_show: int = 0
    model_config = ConfigDict(from_attributes=True)


class RevenueStatsSchema(BaseModel):
    total_revenue: float = 0.0
    gross_revenue: float = 0.0
    net_revenue: float = 0.0
    pending_revenue: float = 0.0
    refunded_amount: float = 0.0
    total_refunded: float = 0.0
    currency: str = "INR"
    model_config = ConfigDict(from_attributes=True)


class PropertyStatsSchema(BaseModel):
    total: int = 0
    active: int = 0
    draft: int = 0
    inactive: int = 0
    archived: int = 0
    featured: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)


class UserStatsSchema(BaseModel):
    total: int = 0
    active: int = 0
    inactive: int = 0
    suspended: int = 0
    by_role: Dict[str, int] = Field(default_factory=dict)
    pending_hosts: int = 0
    model_config = ConfigDict(from_attributes=True)


class RefundStatsSchema(BaseModel):
    total_requests: int = 0
    pending: int = 0
    approved: int = 0
    processed: int = 0
    rejected: int = 0
    total_amount_refunded: float = 0.0
    model_config = ConfigDict(from_attributes=True)


class ReviewStatsSchema(BaseModel):
    total_reviews: int = 0
    average_rating: float = 0.0
    model_config = ConfigDict(from_attributes=True)


class OccupancyTodaySchema(BaseModel):
    today_check_ins: int = 0
    today_check_outs: int = 0
    active_guests: int = 0
    model_config = ConfigDict(from_attributes=True)


class RevenueTrendItemSchema(BaseModel):
    month: str
    revenue: float = 0.0
    gross_revenue: float = 0.0
    refunded: float = 0.0
    bookings_count: int = 0
    model_config = ConfigDict(from_attributes=True)



class RecentBookingSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    booking_reference: str
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    property_name: Optional[str] = None
    property_slug: Optional[str] = None
    check_in_date: date
    check_out_date: date
    num_guests: int = 1
    num_rooms: int = 1
    total_amount: float = 0.0
    currency: str = "INR"
    status: str
    payment_status: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)

    @field_validator("total_amount", mode="before")
    @classmethod
    def validate_amount(cls, value):
        if value is None:
            return 0.0
        return float(value)


class RecentHostRequestSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: str
    email: str
    phone: Optional[str] = None
    property_name: Optional[str] = None
    property_type: Optional[str] = None
    city: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class RecentUserSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: Optional[str] = None
    email: str
    role: str
    status: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)


class TopPropertySchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str
    slug: Optional[str] = None
    city: Optional[str] = None
    type: Optional[str] = None
    price_per_night: Optional[float] = 0.0
    image_url: Optional[str] = None
    total_bookings: int = 0
    total_revenue: float = 0.0
    average_rating: Optional[float] = 0.0
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        return str(value)

    @field_validator("price_per_night", "total_revenue", "average_rating", mode="before")
    @classmethod
    def validate_floats(cls, value):
        if value is None:
            return 0.0
        return float(value)


# ─────────────────────────────────────────────
# Full Dashboard Data & Response Schemas
# ─────────────────────────────────────────────

class AdminDashboardDataSchema(BaseModel):
    bookings_summary: BookingStatsSchema
    revenue_summary: RevenueStatsSchema
    properties_summary: PropertyStatsSchema
    users_summary: UserStatsSchema
    refunds_summary: RefundStatsSchema
    occupancy_today: OccupancyTodaySchema
    revenue_trends: List[RevenueTrendItemSchema] = Field(default_factory=list)
    recent_bookings: List[RecentBookingSchema] = Field(default_factory=list)
    recent_host_requests: List[RecentHostRequestSchema] = Field(default_factory=list)
    recent_users: List[RecentUserSchema] = Field(default_factory=list)
    top_properties: List[TopPropertySchema] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class AdminDashboardResponseSchema(BaseResponse):
    data: AdminDashboardDataSchema


class VendorDashboardDataSchema(BaseModel):
    bookings_summary: BookingStatsSchema
    revenue_summary: RevenueStatsSchema
    properties_summary: PropertyStatsSchema
    reviews_summary: ReviewStatsSchema
    occupancy_today: OccupancyTodaySchema
    revenue_trends: List[RevenueTrendItemSchema] = Field(default_factory=list)
    recent_bookings: List[RecentBookingSchema] = Field(default_factory=list)
    upcoming_bookings: List[RecentBookingSchema] = Field(default_factory=list)
    top_properties: List[TopPropertySchema] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class VendorDashboardResponseSchema(BaseResponse):
    data: VendorDashboardDataSchema


# ─────────────────────────────────────────────
# Summary Schemas for lightweight calls
# ─────────────────────────────────────────────

class AdminSummaryDataSchema(BaseModel):
    bookings_summary: BookingStatsSchema
    revenue_summary: RevenueStatsSchema
    properties_summary: PropertyStatsSchema
    users_summary: UserStatsSchema
    refunds_summary: RefundStatsSchema
    occupancy_today: OccupancyTodaySchema
    model_config = ConfigDict(from_attributes=True)


class AdminSummaryResponseSchema(BaseResponse):
    data: AdminSummaryDataSchema


class VendorSummaryDataSchema(BaseModel):
    bookings_summary: BookingStatsSchema
    revenue_summary: RevenueStatsSchema
    properties_summary: PropertyStatsSchema
    reviews_summary: ReviewStatsSchema
    occupancy_today: OccupancyTodaySchema
    model_config = ConfigDict(from_attributes=True)


class VendorSummaryResponseSchema(BaseResponse):
    data: VendorSummaryDataSchema

