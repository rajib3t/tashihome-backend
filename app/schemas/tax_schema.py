from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, AliasChoices, field_validator
from app.schemas.response import BaseResponse, PaginationResponse


class TaxSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    name: str
    code: str
    rate: float
    tax_type: str
    is_inclusive: bool
    is_default: bool
    gst_number: Optional[str] = None
    legal_name: Optional[str] = None
    address: Optional[str] = None
    hsn_sac_code: Optional[str] = None
    cgst_rate: Optional[float] = None
    sgst_rate: Optional[float] = None
    igst_rate: Optional[float] = None
    description: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)

    @field_validator("rate", "cgst_rate", "sgst_rate", "igst_rate", mode="before")
    @classmethod
    def validate_rates(cls, value):
        if value is None:
            return None
        return float(value)

    @field_validator("status", "tax_type", mode="before")
    @classmethod
    def validate_enums(cls, value):
        if hasattr(value, "value"):
            return value.value
        return str(value) if value is not None else None


class TaxResponseSchema(BaseResponse):
    data: Optional[TaxSchema] = None


class TaxListResponseSchema(PaginationResponse):
    data: List[TaxSchema] = []


class PublicTaxListResponseSchema(BaseResponse):
    data: List[TaxSchema] = []

