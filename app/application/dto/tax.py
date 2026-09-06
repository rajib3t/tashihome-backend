from typing import Optional, Union, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.exceptions import AppException
from app.models.tax_model import TaxStatus, TaxType


class TaxCreateDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    rate: float = Field(..., ge=0.0, le=100.0)
    tax_type: Optional[TaxType] = TaxType.PERCENTAGE
    is_inclusive: Optional[bool] = False
    is_default: Optional[bool] = False
    gst_number: Optional[str] = None
    legal_name: Optional[str] = None
    address: Optional[str] = None
    hsn_sac_code: Optional[str] = None
    cgst_rate: Optional[float] = None
    sgst_rate: Optional[float] = None
    igst_rate: Optional[float] = None
    description: Optional[str] = None
    status: Optional[TaxStatus] = TaxStatus.ACTIVE

    @field_validator("tax_type", mode="before")
    @classmethod
    def parse_tax_type(cls, v):
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in TaxType.__members__:
                return TaxType[v_upper]
            v_lower = v.strip().lower()
            for member in TaxType:
                if member.value.lower() == v_lower:
                    return member
        return v

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in TaxStatus.__members__:
                return TaxStatus[v_upper]
            v_lower = v.strip().lower()
            for member in TaxStatus:
                if member.value.lower() == v_lower:
                    return member
        return v

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise AppException(
                status_code=422,
                message="Tax code cannot be empty.",
                field="code",
                error_code="TAX_CODE_EMPTY",
            )
        return v.strip().upper().replace(" ", "_")


class TaxUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    code: Optional[str] = None
    rate: Optional[float] = None
    tax_type: Optional[TaxType] = None
    is_inclusive: Optional[bool] = None
    is_default: Optional[bool] = None
    gst_number: Optional[str] = None
    legal_name: Optional[str] = None
    address: Optional[str] = None
    hsn_sac_code: Optional[str] = None
    cgst_rate: Optional[float] = None
    sgst_rate: Optional[float] = None
    igst_rate: Optional[float] = None
    description: Optional[str] = None
    status: Optional[TaxStatus] = None

    @field_validator("tax_type", mode="before")
    @classmethod
    def parse_tax_type(cls, v):
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in TaxType.__members__:
                return TaxType[v_upper]
            v_lower = v.strip().lower()
            for member in TaxType:
                if member.value.lower() == v_lower:
                    return member
        return v

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in TaxStatus.__members__:
                return TaxStatus[v_upper]
            v_lower = v.strip().lower()
            for member in TaxStatus:
                if member.value.lower() == v_lower:
                    return member
        return v

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise AppException(
                    status_code=422,
                    message="Tax code cannot be empty.",
                    field="code",
                    error_code="TAX_CODE_EMPTY",
                )
            return v.strip().upper().replace(" ", "_")
        return v


class TaxStatusUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: TaxStatus

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in TaxStatus.__members__:
                return TaxStatus[v_upper]
            v_lower = v.strip().lower()
            for member in TaxStatus:
                if member.value.lower() == v_lower:
                    return member
        return v


class TaxQueryDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    page: int = 1
    size: int = 20
    search: Optional[str] = None
    status: Optional[str] = None
    is_default: Optional[bool] = None

    @field_validator("page", "size")
    @classmethod
    def validate_positive(cls, value: int, info) -> int:
        if value < 1:
            raise AppException(
                status_code=422,
                message=f"{info.field_name} must be greater than 0.",
                field=info.field_name,
                error_code="INVALID_PAGINATION",
            )
        return value

