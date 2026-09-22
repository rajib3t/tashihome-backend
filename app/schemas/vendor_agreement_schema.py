from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse, PaginationResponse


class AgreementClauseSchema(BaseModel):
    heading: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class SignatureFontOptionSchema(BaseModel):
    id: str
    name: str
    font_family: str
    category: str

    model_config = ConfigDict(from_attributes=True)


AVAILABLE_SIGNATURE_FONTS = [
    SignatureFontOptionSchema(id="dancing_script", name="Dancing Script", font_family="'Dancing Script', cursive", category="Cursive & Fluid"),
    SignatureFontOptionSchema(id="great_vibes", name="Great Vibes", font_family="'Great Vibes', cursive", category="Classic Calligraphy"),
    SignatureFontOptionSchema(id="caveat", name="Caveat", font_family="'Caveat', cursive", category="Modern Handwritten"),
    SignatureFontOptionSchema(id="sacramento", name="Sacramento", font_family="'Sacramento', cursive", category="Monoline Script"),
    SignatureFontOptionSchema(id="parisienne", name="Parisienne", font_family="'Parisienne', cursive", category="Casual Chic"),
    SignatureFontOptionSchema(id="alex_brush", name="Alex Brush", font_family="'Alex Brush', cursive", category="Traditional Elegance"),
]


class AgreementVendorCompanyData(BaseModel):
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AgreementVendorData(BaseModel):
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[AgreementVendorCompanyData] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)

    model_config = ConfigDict(from_attributes=True)


class VendorAgreementData(BaseModel):
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    template_id: Optional[str | int] = None
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
    signature_font: Optional[str] = None
    document_hash: Optional[str] = None
    pdf_file_url: Optional[str] = None
    first_party_signer_name: Optional[str] = None
    first_party_signer_role: Optional[str] = None
    first_party_signature_type: Optional[str] = None
    first_party_signature_data: Optional[str] = None
    first_party_signature_font: Optional[str] = None
    first_party_signed_at: Optional[datetime] = None
    is_first_party_signed: Optional[bool] = None
    is_second_party_signed: Optional[bool] = None
    is_bilateral_signed: Optional[bool] = None
    created_at: Optional[datetime] = None
    vendor: Optional[AgreementVendorData] = None

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
    signature_font: Optional[str] = None
    document_hash: Optional[str] = None
    signer_ip: Optional[str] = None
    sent_at: Optional[datetime] = None
    first_party_signer_name: Optional[str] = None
    first_party_signer_role: Optional[str] = None
    first_party_signature_type: Optional[str] = None
    first_party_signature_data: Optional[str] = None
    first_party_signature_font: Optional[str] = None
    first_party_signed_at: Optional[datetime] = None
    is_first_party_signed: Optional[bool] = None
    is_second_party_signed: Optional[bool] = None
    is_bilateral_signed: Optional[bool] = None
    operator_name: Optional[str] = None
    operator_legal_name: Optional[str] = None
    operator_logo_url: Optional[str] = None
    operator_address: Optional[str] = None
    available_signature_fonts: List[SignatureFontOptionSchema] = Field(default_factory=lambda: list(AVAILABLE_SIGNATURE_FONTS))

    model_config = ConfigDict(from_attributes=True)


class VendorAgreementResponseSchema(BaseResponse):
    data: VendorAgreementData


class VendorAgreementListResponseSchema(PaginationResponse):
    data: List[VendorAgreementData]


class PublicAgreementResponseSchema(BaseResponse):
    data: PublicAgreementDetailData


class VendorAgreementDetailData(PublicAgreementDetailData):
    id: Optional[str] = None
    agreement_type: Optional[str] = None
    pdf_file_url: Optional[str] = None
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    signature_type: Optional[str] = None
    signature_data: Optional[str] = None
    signature_font: Optional[str] = None
    document_hash: Optional[str] = None
    signer_ip: Optional[str] = None
    created_at: Optional[datetime] = None


class VendorMyAgreementResponseSchema(BaseResponse):
    data: Optional[VendorAgreementDetailData] = None

