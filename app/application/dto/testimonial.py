from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TestimonialCreateDTO(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Author display name (defaults to user name if empty)")
    designation: Optional[str] = Field(None, max_length=255, description="e.g. Traveler, Homestay Host, Guest")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar or profile image URL")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    content: str = Field(..., min_length=5, max_length=3000, description="Testimonial message/content")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Testimonial content cannot be empty")
        return v

    @field_validator("name", "designation", "avatar_url")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None


class TestimonialUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    designation: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    rating: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[str] = Field(None, min_length=5, max_length=3000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Testimonial content cannot be empty")
            return v
        return None

    @field_validator("name", "designation", "avatar_url")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None


class TestimonialStatusUpdateDTO(BaseModel):
    status: str = Field(..., description="New status: pending, approved, rejected, hidden")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"pending", "approved", "rejected", "hidden"}
        v_clean = v.strip().lower()
        if v_clean not in allowed:
            raise ValueError(f"Invalid testimonial status '{v}'. Allowed: {sorted(allowed)}")
        return v_clean


class TestimonialFeatureToggleDTO(BaseModel):
    is_featured: bool = Field(..., description="Whether to feature this testimonial on homepage")


class TestimonialQueryDTO(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    status: Optional[str] = None
    user_role: Optional[str] = None
    is_featured: Optional[bool] = None
    search: Optional[str] = None
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

