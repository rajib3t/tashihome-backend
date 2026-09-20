from datetime import datetime, timezone
from typing import Any
from app.core.events import DomainEvent
from app.models.vendor_agreement_model import VendorAgreement


class AgreementInvitationSentEvent(DomainEvent):
    def __init__(
        self,
        agreement: VendorAgreement,
        recipient_name: str,
        recipient_email: str,
    ):
        vendor = getattr(agreement, "vendor", None)
        company = getattr(vendor, "company", None) if vendor else None
        company_name = getattr(company, "name", None) if company else None

        valid_days = 7
        expires_at = getattr(agreement, "expires_at", None)
        if expires_at and hasattr(expires_at, "timestamp"):
            try:
                now = datetime.now(timezone.utc)
                delta = expires_at - now
                valid_days = max(1, round(delta.total_seconds() / 86400))
            except Exception:
                valid_days = 7

        payload = {
            "agreement_id": int(agreement.id) if hasattr(agreement, "id") and agreement.id else None,
            "public_id": str(agreement.public_id),
            "token": agreement.token,
            "recipient_name": recipient_name,
            "recipient_email": recipient_email,
            "company_name": company_name or f"{recipient_name}'s Homestay",
            "commission_percentage": float(agreement.commission_percentage) if getattr(agreement, "commission_percentage", None) is not None else 10.0,
            "expires_at": expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at),
            "expires_in_days": valid_days,
        }
        super().__init__(name="agreement.invitation_sent", payload=payload)

