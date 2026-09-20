from __future__ import annotations

import json
import logging
from typing import Optional

from app.application.dto.agreements.agreement_dto import SignAgreementDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.schemas.vendor_agreement_schema import AgreementClauseSchema, PublicAgreementDetailData
from app.services.agreement_pdf_service import DEFAULT_HOST_CLAUSES
from app.services.vendor_agreement_service import VendorAgreementService

logger = logging.getLogger(__name__)


class SignAgreementUseCase(BaseUseCase):
    def __init__(self, agreement_service: VendorAgreementService):
        self.agreement_service = agreement_service

    async def execute(
        self,
        token: str,
        sign_dto: SignAgreementDTO,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        current_user: Optional[CurrentUser] = None,
    ) -> PublicAgreementDetailData:
        agreement = await self.agreement_service.sign_agreement(
            token=token,
            sign_dto=sign_dto,
            client_ip=client_ip,
            user_agent=user_agent,
            authenticated_user_id=current_user.id if current_user else None,
            authenticated_user_role=current_user.role if current_user else None,
        )

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

        return PublicAgreementDetailData(
            token=agreement.token,
            title=agreement.title,
            version=agreement.version,
            status=agreement.status.value,
            commission_percentage=float(agreement.commission_percentage),
            expires_at=agreement.expires_at,
            host_name=str(agreement.signer_name or (getattr(vendor, "full_name", "") or "Host Partner")),
            host_email=str(getattr(vendor, "email", "") or getattr(agreement, "signer_email", "") or ""),
            host_phone=str(vendor.phone) if getattr(vendor, "phone", None) else None,
            company_name=str(getattr(company, "name", None) or f"{getattr(vendor, 'full_name', '') or 'Host'}'s Homestay"),
            city=city,
            property_address=prop_address,
            terms_clauses=terms_clauses,
            pdf_download_url=pdf_url,
            signed_at=agreement.signed_at,
            operator_name=operator_info.get("app_name"),
            operator_legal_name=operator_info.get("legal_name"),
            operator_logo_url=operator_info.get("logo_url"),
            operator_address=operator_info.get("address"),
        )

