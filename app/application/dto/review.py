from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReviewCreateDTO(BaseModel):
    booking_id: Optional[str] = Field(None, description="Public UUID or Reference of the booking to review")
    booking_reference: Optional[str] = Field(None, description="Booking reference code (optional alternative to booking_id)")
    rating: int = Field(..., ge=1, le=5, description="Star rating between 1 and 5")
    comment: Optional[str] = Field(None, max_length=2000, description="Review feedback comments")

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None

    @field_validator("booking_id", "booking_reference")
    @classmethod
    def strip_booking_identifier(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None


class ReviewUpdateDTO(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating between 1 and 5")
    comment: Optional[str] = Field(None, max_length=2000, description="Review feedback comments")

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None


class ReviewHostReplyDTO(BaseModel):
    host_reply: str = Field(..., min_length=1, max_length=2000, description="Vendor / Host reply to the review")

    @field_validator("host_reply")
    @classmethod
    def validate_host_reply(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Host reply cannot be empty")
        return v


class ReviewStatusUpdateDTO(BaseModel):
    status: str = Field(..., description="New status: pending, published, hidden, flagged, rejected")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"pending", "published", "hidden", "flagged", "rejected"}
        v_clean = v.strip().lower()
        if v_clean not in allowed:
            raise ValueError(f"Invalid review status '{v}'. Allowed: {sorted(allowed)}")
        return v_clean


class ReviewQueryDTO(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    status: Optional[str] = None
    property_id: Optional[str] = None
    search: Optional[str] = None
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

