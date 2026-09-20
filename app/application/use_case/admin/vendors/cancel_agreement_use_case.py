from __future__ import annotations

import logging
from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.models.vendor_agreement_model import VendorAgreement
from app.services.vendor_agreement_service import VendorAgreementService

logger = logging.getLogger(__name__)


class CancelAgreementUseCase(BaseUseCase):
    def __init__(
        self,
        agreement_service: VendorAgreementService,
        current_user: CurrentUser,
    ):
        self.agreement_service = agreement_service
        self.current_user = current_user

    async def execute(self, agreement_id: str) -> VendorAgreement:
        return await self.agreement_service.cancel_agreement(agreement_id)

