from datetime import datetime
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse, PaginationResponse


class TestimonialUserSchema(BaseModel):
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


class TestimonialSchema(BaseModel):
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str
    designation: Optional[str] = None
    avatar_url: Optional[str] = None
    rating: Optional[int] = None
    content: str
    status: str
    user_role: str
    is_featured: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    user: Optional[TestimonialUserSchema] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        return str(value) if value is not None else None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value):
        return value.value if hasattr(value, "value") else str(value)


class TestimonialResponseSchema(BaseResponse):
    data: TestimonialSchema


class TestimonialListResponseSchema(PaginationResponse):
    data: List[TestimonialSchema]

