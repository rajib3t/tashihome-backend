from typing import Any, Dict

from app.application.dto.payouts.payout import CalculateVendorEarningsDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.config import settings
from app.core.exceptions import AppException
from app.services.payout_service import PayoutService
from app.services.user_service import UserService


class CalculateVendorEarningsUseCase(BaseUseCase):
    def __init__(
        self,
        payout_service: PayoutService,
        user_service: UserService,
    ):
        self.payout_service = payout_service
        self.user_service = user_service

    async def execute(self, params: CalculateVendorEarningsDTO) -> Dict[str, Any]:
        vendor = await self.user_service.get_user_by_public_id(params.vendor_id)
        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found.",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        commission_pct = (
            params.commission_percentage
            if params.commission_percentage is not None
            else settings.DEFAULT_COMMISSION_PERCENTAGE
        )

        summary = await self.payout_service.calculate_vendor_earnings(
            vendor_id=vendor.id,
            period_start=params.period_start,
            period_end=params.period_end,
            commission_percentage=commission_pct,
        )

        summary["vendor_public_id"] = vendor.public_id
        summary["vendor_name"] = vendor.full_name
        summary["vendor_email"] = vendor.email

        return summary

