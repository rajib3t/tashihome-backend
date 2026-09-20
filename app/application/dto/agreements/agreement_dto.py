from typing import List, Optional
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class SendVendorAgreementDTO:
    commission_percentage: Optional[float] = None
    valid_days: int = 7
    custom_notes: Optional[str] = None
    agreement_type: str = "host_onboarding"


@dataclass(config=ConfigDict(extra="forbid"))
class SignAgreementDTO:
    signer_name: str
    signature_type: str  # 'drawn' | 'typed'
    signature_data: str  # base64 PNG data URL or typed text
    signature_font: Optional[str] = "dancing_script"  # font key (e.g. 'dancing_script', 'great_vibes', etc.)
    terms_accepted: bool = True
    consent_acknowledged: bool = True


@dataclass(config=ConfigDict(extra="forbid"))
class AgreementFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class AgreementQueryDTO:
    page: int = 1
    size: int = 10
    status: Optional[str] = None
    search: Optional[str] = None
    vendor_id: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    filters: Optional[List[AgreementFilterDTO]] = None


@dataclass(config=ConfigDict(extra="forbid"))
class AdminCountersignAgreementDTO:
    signer_name: Optional[str] = None
    signer_role: Optional[str] = "Platform Authorized Signatory"
    signature_type: Optional[str] = "digital"  # 'digital' | 'drawn' | 'typed'
    signature_data: Optional[str] = None
    signature_font: Optional[str] = None


