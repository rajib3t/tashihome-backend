from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.payout_model import Payout, PayoutStatus
from app.services.payout_service import PayoutService
from app.services.razorpay_service import RazorpayService

_RELATIONS = {
    "vendor": True,
    "bank_account": True,
    "creator": True,
}


class CancelPayoutUseCase(BaseUseCase):
    def __init__(
        self,
        payout_service: PayoutService,
        razorpay_service: RazorpayService,
    ):
        self.payout_service = payout_service
        self.razorpay_service = razorpay_service

    async def execute(self, payout_id: str) -> Payout:
        payout = await self.payout_service.get_by_public_id(
            payout_id,
            with_relations=_RELATIONS,
        )
        if not payout:
            raise AppException(
                status_code=404,
                message="Payout record not found.",
                error_code="PAYOUT_NOT_FOUND",
                field="payout_id",
            )

        if payout.status == PayoutStatus.PAID:
            raise AppException(
                status_code=400,
                message="Cannot cancel a payout that has already been paid.",
                error_code="PAYOUT_ALREADY_PAID",
            )

        if payout.status == PayoutStatus.CANCELLED:
            return payout

        # If it was sent to Razorpay and is in queue/processing, attempt Razorpay cancel
        if payout.razorpay_payout_id and payout.status == PayoutStatus.PROCESSING:
            try:
                await self.razorpay_service.cancel_payout(payout.razorpay_payout_id)
            except AppException:
                # If Razorpay cancellation cannot proceed (already in flight), log and propagate or mark cancelled locally
                pass

        payout.status = PayoutStatus.CANCELLED
        return await self.payout_service.update(payout, with_relations=_RELATIONS)

