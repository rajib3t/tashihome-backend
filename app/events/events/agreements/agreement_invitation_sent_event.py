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
        payload = {
            "agreement_id": int(agreement.id) if hasattr(agreement, "id") and agreement.id else None,
            "public_id": str(agreement.public_id),
            "token": agreement.token,
            "recipient_name": recipient_name,
            "recipient_email": recipient_email,
            "commission_percentage": float(agreement.commission_percentage) if getattr(agreement, "commission_percentage", None) is not None else 10.0,
            "expires_at": agreement.expires_at.isoformat() if hasattr(getattr(agreement, "expires_at", None), "isoformat") else str(agreement.expires_at),
        }
        super().__init__(name="agreement.invitation_sent", payload=payload)

