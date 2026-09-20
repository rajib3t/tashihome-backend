from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse


class AgreementClauseSchema(BaseModel):
    heading: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class VendorAgreementData(BaseModel):
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    title: str
    version: str
    status: str
    agreement_type: str
    token: str
    commission_percentage: float
    expires_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    signer_phone: Optional[str] = None
    signature_type: Optional[str] = None
    document_hash: Optional[str] = None
    pdf_file_url: Optional[str] = None
    first_party_signer_name: Optional[str] = None
    first_party_signer_role: Optional[str] = None
    first_party_signature_type: Optional[str] = None
    first_party_signature_data: Optional[str] = None
    first_party_signed_at: Optional[datetime] = None
    is_first_party_signed: Optional[bool] = None
    is_second_party_signed: Optional[bool] = None
    is_bilateral_signed: Optional[bool] = None
    created_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)

    model_config = ConfigDict(from_attributes=True)


class PublicAgreementDetailData(BaseModel):
    token: str
    title: str
    version: str
    status: str
    commission_percentage: float
    expires_at: Optional[datetime] = None
    host_name: str
    host_email: str
    host_phone: Optional[str] = None
    company_name: str
    city: Optional[str] = None
    property_address: Optional[str] = None
    terms_clauses: List[AgreementClauseSchema]
    pdf_download_url: Optional[str] = None
    signed_at: Optional[datetime] = None
    signer_name: Optional[str] = None
    signature_type: Optional[str] = None
    signature_data: Optional[str] = None
    document_hash: Optional[str] = None
    signer_ip: Optional[str] = None
    sent_at: Optional[datetime] = None
    first_party_signer_name: Optional[str] = None
    first_party_signer_role: Optional[str] = None
    first_party_signature_type: Optional[str] = None
    first_party_signature_data: Optional[str] = None
    first_party_signed_at: Optional[datetime] = None
    is_first_party_signed: Optional[bool] = None
    is_second_party_signed: Optional[bool] = None
    is_bilateral_signed: Optional[bool] = None
    operator_name: Optional[str] = None
    operator_legal_name: Optional[str] = None
    operator_logo_url: Optional[str] = None
    operator_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VendorAgreementResponseSchema(BaseResponse):
    data: VendorAgreementData


class VendorAgreementListResponseSchema(BaseResponse):
    data: List[VendorAgreementData]


class PublicAgreementResponseSchema(BaseResponse):
    data: PublicAgreementDetailData


class VendorAgreementDetailData(PublicAgreementDetailData):
    id: Optional[str] = None
    agreement_type: Optional[str] = None
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    signature_type: Optional[str] = None
    signature_data: Optional[str] = None
    document_hash: Optional[str] = None
    signer_ip: Optional[str] = None
    created_at: Optional[datetime] = None


class VendorMyAgreementResponseSchema(BaseResponse):
    data: Optional[VendorAgreementDetailData] = None

