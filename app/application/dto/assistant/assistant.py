import re
from datetime import date, timedelta
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class AssistantMessageDTO(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str = Field(..., min_length=1, max_length=4000, description="Message content.")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v_clean = v.strip() if isinstance(v, str) else ""
        if not v_clean:
            raise ValueError("Message content cannot be empty or only whitespace.")
        return v_clean


class AssistantChatRequestDTO(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's query or instruction for the AI assistant.",
    )
    conversation_history: Optional[List[AssistantMessageDTO]] = Field(
        default_factory=list,
        max_length=50,
        description="Previous turns in the conversation for conversational context.",
    )
    session_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Optional conversation session identifier.",
    )
    page: Optional[int] = Field(default=None, ge=1, le=100, description="Optional page number for search results.")
    page_size: Optional[int] = Field(default=None, ge=1, le=30, description="Optional page size for search results.")
    guest_name: Optional[str] = Field(default=None, max_length=100, description="Guest full name if unauthenticated.")
    guest_email: Optional[EmailStr] = Field(default=None, description="Guest email if unauthenticated.")
    guest_phone: Optional[str] = Field(default=None, max_length=25, description="Guest phone number if unauthenticated.")
    guest_password: Optional[str] = Field(default=None, min_length=6, max_length=128, description="Optional password if creating account.")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v_clean = v.strip() if isinstance(v, str) else ""
        if not v_clean:
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return v_clean

    @field_validator("session_id", "guest_name")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip()
        return v_clean if v_clean else None

    @field_validator("guest_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip()
        if not v_clean:
            return None
        if not re.match(r"^\+?[0-9\s\-()]{5,25}$", v_clean):
            raise ValueError("Invalid phone number format.")
        return v_clean


class AssistantCheckoutDTO(BaseModel):
    property_id: str = Field(..., min_length=1, max_length=255, description="Homestay slug, public UUID, or ID.")
    check_in_date: date = Field(..., description="Check-in date (YYYY-MM-DD).")
    check_out_date: date = Field(..., description="Check-out date (YYYY-MM-DD).")
    num_guests: int = Field(default=1, ge=1, le=50, description="Number of guests.")
    num_rooms: int = Field(default=1, ge=1, le=50, description="Number of rooms.")
    room_type_id: Optional[str] = Field(default=None, max_length=255, description="Room type ID or public UUID.")
    special_requests: Optional[str] = Field(default=None, max_length=1000, description="Special requests or notes.")
    guest_name: Optional[str] = Field(default=None, max_length=100, description="Guest name (required if unauthenticated).")
    guest_email: Optional[EmailStr] = Field(default=None, description="Guest email (required if unauthenticated).")
    guest_phone: Optional[str] = Field(default=None, max_length=25, description="Guest phone (required if unauthenticated).")
    guest_password: Optional[str] = Field(default=None, min_length=6, max_length=128, description="Optional password for registration.")

    @field_validator("property_id")
    @classmethod
    def validate_prop_id(cls, v: str) -> str:
        v_clean = v.strip() if isinstance(v, str) else ""
        if not v_clean:
            raise ValueError("property_id cannot be empty.")
        return v_clean

    @field_validator("guest_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip()
        if not v_clean:
            return None
        if not re.match(r"^\+?[0-9\s\-()]{5,25}$", v_clean):
            raise ValueError("Invalid phone number format.")
        return v_clean

    @model_validator(mode="after")
    def validate_stay_dates(self) -> "AssistantCheckoutDTO":
        today = date.today()
        if self.check_in_date < today:
            raise ValueError("Check-in date cannot be in the past.")
        if self.check_out_date <= self.check_in_date:
            raise ValueError("Check-out date must be strictly after check-in date.")
        if (self.check_out_date - self.check_in_date).days > 90:
            raise ValueError("Maximum reservation duration cannot exceed 90 days.")
        return self


class AssistantSearchDTO(BaseModel):
    query: Optional[str] = Field(default=None, max_length=500, description="Natural language search, homestay name, or destination name.")
    city_name: Optional[str] = Field(default=None, max_length=100, description="Filter by city name.")
    location_name: Optional[str] = Field(default=None, max_length=100, description="Filter by neighborhood or location area.")
    address: Optional[str] = Field(default=None, max_length=255, description="Filter by street address or road name.")
    check_in_date: Optional[date] = Field(default=None, description="Check-in date.")
    check_out_date: Optional[date] = Field(default=None, description="Check-out date.")
    guests: Optional[int] = Field(default=None, ge=1, le=50, description="Guests count.")
    rooms: Optional[int] = Field(default=1, ge=1, le=50, description="Rooms count.")
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum price per night.")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price per night.")
    property_type: Optional[str] = Field(default=None, max_length=50, description="Property type.")
    page: int = Field(default=1, ge=1, le=100)
    page_size: int = Field(default=10, ge=1, le=30)

    @field_validator("query", "city_name", "location_name", "address", "property_type")
    @classmethod
    def sanitize_search_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip()
        return v_clean if v_clean else None

    @model_validator(mode="after")
    def validate_search_constraints(self) -> "AssistantSearchDTO":
        if self.check_in_date and self.check_in_date < date.today():
            raise ValueError("Check-in date cannot be in the past.")
        if self.check_in_date and self.check_out_date and self.check_out_date <= self.check_in_date:
            raise ValueError("Check-out date must be strictly after check-in date.")
        if self.min_price is not None and self.max_price is not None and self.max_price < self.min_price:
            raise ValueError("Maximum price must be greater than or equal to minimum price.")
        return self


class SemanticSearchRequestDTO(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Descriptive or vibe-based natural language query (e.g., 'cozy wooden stay with mountain view').",
    )
    city_name: Optional[str] = Field(default=None, max_length=100, description="Optional city or dzongkhag filter.")
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum price filter.")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price filter.")
    property_type: Optional[str] = Field(default=None, max_length=50, description="Optional property type filter.")
    limit: int = Field(default=8, ge=1, le=50, description="Maximum results to return.")
    min_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum cosine similarity threshold.")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v_clean = v.strip() if isinstance(v, str) else ""
        if not v_clean:
            raise ValueError("Search query cannot be empty or only whitespace.")
        return v_clean

    @field_validator("city_name", "property_type")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip()
        return v_clean if v_clean else None

    @model_validator(mode="after")
    def validate_prices(self) -> "SemanticSearchRequestDTO":
        if self.min_price is not None and self.max_price is not None and self.max_price < self.min_price:
            raise ValueError("Maximum price must be greater than or equal to minimum price.")
        return self

