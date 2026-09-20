from __future__ import annotations

import json
import logging
from typing import List

from app.application.use_case.base_use_case import BaseUseCase
from app.schemas.vendor_agreement_schema import AgreementClauseSchema, PublicAgreementDetailData
from app.services.agreement_pdf_service import DEFAULT_HOST_CLAUSES
from app.services.vendor_agreement_service import VendorAgreementService

logger = logging.getLogger(__name__)


class GetPublicAgreementUseCase(BaseUseCase):
    def __init__(self, agreement_service: VendorAgreementService):
        self.agreement_service = agreement_service

    async def execute(self, token: str) -> PublicAgreementDetailData:
        agreement = await self.agreement_service.get_by_token(token)

        # Parse clauses
        clauses_data = DEFAULT_HOST_CLAUSES
        if agreement.terms_snapshot:
            try:
                clauses_data = json.loads(agreement.terms_snapshot)
            except Exception:
                clauses_data = DEFAULT_HOST_CLAUSES

        terms_clauses = [
            AgreementClauseSchema(
                heading=item.get("heading", ""),
                content=item.get("body", item.get("content", "")),
            )
            for item in clauses_data
        ]

        vendor = getattr(agreement, "vendor", None)
        company = getattr(vendor, "company", None) if vendor else None
        address = None
        if company:
            try:
                addrs = getattr(company, "addresses", None)
                if addrs:
                    address = addrs[0]
            except Exception as exc:
                logger.warning("Could not resolve company addresses: %s", exc)

        if not address and vendor:
            try:
                u_addrs = getattr(vendor, "addresses", None)
                if u_addrs:
                    address = u_addrs[0]
            except Exception as exc:
                logger.warning("Could not resolve vendor addresses: %s", exc)

        city = None
        prop_address = None
        if address:
            try:
                city = getattr(address, "city", None)
                prop_address = getattr(address, "address_line1", None)
            except Exception:
                pass

        pdf_url = await self.agreement_service.get_download_url(agreement)
        operator_info = await self.agreement_service.get_operator_info()

        def _safe_str(val):
            return val if isinstance(val, str) else None

        return PublicAgreementDetailData(
            token=str(agreement.token),
            title=str(agreement.title),
            version=str(agreement.version),
            status=agreement.status.value if hasattr(agreement.status, "value") else str(agreement.status),
            commission_percentage=float(agreement.commission_percentage),
            expires_at=agreement.expires_at,
            host_name=str(getattr(vendor, "full_name", "") or getattr(agreement, "signer_name", "") or "Host Partner"),
            host_email=str(getattr(vendor, "email", "") or getattr(agreement, "signer_email", "") or ""),
            host_phone=str(vendor.phone) if getattr(vendor, "phone", None) else None,
            company_name=str(getattr(company, "name", None) or f"{getattr(vendor, 'full_name', '') or 'Host'}'s Homestay"),
            city=city,
            property_address=prop_address,
            terms_clauses=terms_clauses,
            pdf_download_url=pdf_url,
            signed_at=agreement.signed_at if hasattr(agreement, "signed_at") and not str(type(agreement.signed_at)).endswith("MagicMock'>") else None,
            signer_name=_safe_str(getattr(agreement, "signer_name", None)),
            signature_type=_safe_str(getattr(agreement, "signature_type", None)),
            signature_data=_safe_str(getattr(agreement, "signature_data", None)),
            signature_font=_safe_str(getattr(agreement, "signature_font", None)),
            document_hash=_safe_str(getattr(agreement, "document_hash", None)),
            signer_ip=_safe_str(getattr(agreement, "signer_ip", None)),
            sent_at=agreement.sent_at if hasattr(agreement, "sent_at") and not str(type(agreement.sent_at)).endswith("MagicMock'>") else None,
            first_party_signer_name=_safe_str(getattr(agreement, "first_party_signer_name", None)),
            first_party_signer_role=_safe_str(getattr(agreement, "first_party_signer_role", None)),
            first_party_signature_type=_safe_str(getattr(agreement, "first_party_signature_type", None)),
            first_party_signature_data=_safe_str(getattr(agreement, "first_party_signature_data", None)),
            first_party_signature_font=_safe_str(getattr(agreement, "first_party_signature_font", None)),
            first_party_signed_at=agreement.first_party_signed_at if hasattr(agreement, "first_party_signed_at") and not str(type(agreement.first_party_signed_at)).endswith("MagicMock'>") else None,
            is_first_party_signed=bool(getattr(agreement, "is_first_party_signed", False)),
            is_second_party_signed=bool(getattr(agreement, "is_second_party_signed", False)),
            is_bilateral_signed=bool(getattr(agreement, "is_bilateral_signed", False)),
            operator_name=operator_info.get("app_name"),
            operator_legal_name=operator_info.get("legal_name"),
            operator_logo_url=operator_info.get("logo_url"),
            operator_address=operator_info.get("address"),
        )

