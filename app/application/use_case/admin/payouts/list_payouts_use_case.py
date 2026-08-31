from typing import Optional

from app.application.dto.payouts.payout import AdminPayoutQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.payout_model import Payout
from app.repositories.base_repository import Page
from app.services.payout_service import PayoutService
from app.services.user_service import UserService

_RELATIONS = {
    "vendor": True,
    "bank_account": True,
    "creator": True,
}


class ListPayoutsUseCase(BaseUseCase):
    def __init__(
        self,
        payout_service: PayoutService,
        user_service: UserService,
    ):
        self.payout_service = payout_service
        self.user_service = user_service

    async def execute(self, params: AdminPayoutQueryDTO) -> Page[Payout]:
        vendor_internal_id = None
        if params.vendor_id:
            vendor = await self.user_service.get_user_by_public_id(params.vendor_id)
            if not vendor:
                raise AppException(
                    status_code=404,
                    message="Vendor not found.",
                    error_code="VENDOR_NOT_FOUND",
                    field="vendor_id",
                )
            vendor_internal_id = vendor.id

        return await self.payout_service.list_all(
            page=params.page,
            page_size=params.size,
            vendor_id=vendor_internal_id,
            status=params.status,
            period_start=params.period_start,
            period_end=params.period_end,
            sort_order=params.sort_order,
            with_relations=_RELATIONS,
        )

