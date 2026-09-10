from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse, PaginationMeta


class NotificationResponseData(BaseModel):
    id: str = Field(
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    role: str
    type: str
    title: str
    message: str
    data: Optional[dict[str, Any]] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value: Any) -> str:
        if isinstance(value, UUID):
            return str(value)
        return str(value)

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, value: Any) -> str:
        if hasattr(value, "value"):
            return str(value.value)
        return str(value)


class NotificationListPaginationMeta(PaginationMeta):
    total_pages: int
    unread_count: int


class NotificationListResponse(BaseResponse):
    data: list[NotificationResponseData]
    meta: NotificationListPaginationMeta


class NotificationSingleResponse(BaseResponse):
    data: NotificationResponseData


class NotificationUnreadCountResponseData(BaseModel):
    unread_count: int


class NotificationUnreadCountResponse(BaseResponse):
    data: NotificationUnreadCountResponseData


class NotificationMarkAllReadResponse(BaseResponse):
    updated_count: int
