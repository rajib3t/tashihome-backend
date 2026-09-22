from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from app.application.dto.agreements.agreement_dto import SendVendorAgreementDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.vendor_agreement_model import VendorAgreement
from app.services.user_service import UserService
from app.services.vendor_agreement_service import VendorAgreementService

logger = logging.getLogger(__name__)


class SendVendorAgreementUseCase(BaseUseCase):
    def __init__(
        self,
        agreement_service: VendorAgreementService,
        user_service: UserService,
        current_user: CurrentUser,
    ):
        self.agreement_service = agreement_service
        self.user_service = user_service
        self.current_user = current_user

    async def execute(
        self,
        vendor_id: str,
        data: SendVendorAgreementDTO,
    ) -> VendorAgreement:
        # Find vendor by id or public_id
        vendor = None
        if len(vendor_id) == 36:
            try:
                vendor = await self.user_service.get_user_by_public_id(
                    UUID(vendor_id),
                    with_relations={"company": True},
                )
            except Exception:
                vendor = None

        if not vendor and vendor_id.isdigit():
            vendor = await self.user_service.get_user_by_id(
                int(vendor_id),
                with_relations={"company": True},
            )

        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found.",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        agreement = await self.agreement_service.create_and_send_agreement(
            vendor=vendor,
            commission_percentage=data.commission_percentage,
            valid_days=data.valid_days,
            custom_notes=data.custom_notes,
            created_by_id=self.current_user.id,
            commit=True,
            template_id=getattr(data, "template_id", None),
            version=getattr(data, "version", "1.0"),
        )

        return agreement


