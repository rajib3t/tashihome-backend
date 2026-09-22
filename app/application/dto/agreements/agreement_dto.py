from typing import List, Optional
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="ignore"))
class SendVendorAgreementDTO:
    commission_percentage: Optional[float] = None
    valid_days: int = 7
    version: Optional[str] = "1.0"
    custom_notes: Optional[str] = None
    agreement_type: str = "host_onboarding"
    template_id: Optional[str] = None    # public_id of AgreementTemplate to use




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


@dataclass(config=ConfigDict(extra="ignore"))
class AgreementQueryDTO:
    page: int = 1
    size: int = 10
    limit: Optional[int] = None
    status: Optional[str] = None
    search: Optional[str] = None
    vendor_id: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    filters: Optional[List[AgreementFilterDTO]] = None

    def __post_init__(self):
        if self.limit is not None and self.limit > 0:
            self.size = self.limit


@dataclass(config=ConfigDict(extra="forbid"))
class AdminCountersignAgreementDTO:
    signer_name: Optional[str] = None
    signer_role: Optional[str] = "Platform Authorized Signatory"
    signature_type: Optional[str] = "digital"  # 'digital' | 'drawn' | 'typed'
    signature_data: Optional[str] = None
    signature_font: Optional[str] = None


