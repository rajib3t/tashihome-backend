from typing import Any, Optional
from app.core.events import DomainEvent
from app.models.vendor_agreement_model import VendorAgreement


class AgreementCompletedEvent(DomainEvent):
    def __init__(
        self,
        agreement: VendorAgreement,
        pdf_bytes_b64: Optional[str] = None,
    ):
        vendor = getattr(agreement, "vendor", None)
        signer_email = agreement.signer_email or (getattr(vendor, "email", "") if vendor else "")
        signed_at_val = getattr(agreement, "signed_at", None)

        company = getattr(vendor, "company", None) if vendor else None
        company_name = (
            getattr(company, "name", None)
            or (f"{vendor.full_name}'s Homestay" if vendor and getattr(vendor, "full_name", None) else None)
            or (f"{agreement.signer_name}'s Homestay" if agreement.signer_name else "Homestay")
        )

        payload = {
            "agreement_id": int(agreement.id) if hasattr(agreement, "id") and agreement.id else None,
            "public_id": str(agreement.public_id),
            "token": agreement.token,
            "signer_name": agreement.signer_name or (getattr(vendor, "full_name", "Host Partner") if vendor else "Host Partner"),
            "signer_email": signer_email,
            "company_name": company_name,
            "vendor_id": int(agreement.vendor_id) if getattr(agreement, "vendor_id", None) else None,
            "signed_at": signed_at_val.isoformat() if hasattr(signed_at_val, "isoformat") else str(signed_at_val),
            "pdf_file_url": agreement.pdf_file_url,
            "document_hash": agreement.document_hash,
            "pdf_bytes_b64": pdf_bytes_b64,
        }

        super().__init__(name="agreement.completed", payload=payload)

