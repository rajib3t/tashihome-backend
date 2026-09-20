from __future__ import annotations

import logging
from typing import Optional

from app.application.dto.agreements.agreement_dto import AgreementQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.models.vendor_agreement_model import VendorAgreement
from app.repositories.base_repository import Page
from app.services.vendor_agreement_service import VendorAgreementService

logger = logging.getLogger(__name__)


class ListAgreementsUseCase(BaseUseCase):
    def __init__(
        self,
        agreement_service: VendorAgreementService,
        current_user: CurrentUser,
    ):
        self.agreement_service = agreement_service
        self.current_user = current_user

    async def execute(self, params: AgreementQueryDTO) -> Page[VendorAgreement]:
        return await self.agreement_service.list_agreements(params)

