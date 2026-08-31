from datetime import datetime, timezone

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


class SyncRazorpayPayoutUseCase(BaseUseCase):
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

        if not payout.razorpay_payout_id:
            raise AppException(
                status_code=400,
                message="Payout has not been submitted to Razorpay yet.",
                error_code="PAYOUT_NOT_SUBMITTED",
            )

        rzp_response = await self.razorpay_service.fetch_payout(payout.razorpay_payout_id)
        rzp_status = rzp_response.get("status", "").lower()
        payout.utr = rzp_response.get("utr") or payout.utr

        if rzp_status in ["processed", "paid"]:
            payout.status = PayoutStatus.PAID
            if not payout.paid_at:
                payout.paid_at = datetime.now(timezone.utc)
        elif rzp_status in ["queued", "processing", "pending"]:
            payout.status = PayoutStatus.PROCESSING
        elif rzp_status in ["rejected"]:
            payout.status = PayoutStatus.REJECTED
            payout.failure_reason = rzp_response.get("failure_reason")
        elif rzp_status in ["reversed"]:
            payout.status = PayoutStatus.REVERSED
            payout.failure_reason = rzp_response.get("failure_reason")
        elif rzp_status in ["failed"]:
            payout.status = PayoutStatus.FAILED
            payout.failure_reason = rzp_response.get("failure_reason")
        elif rzp_status in ["cancelled"]:
            payout.status = PayoutStatus.CANCELLED

        return await self.payout_service.update(payout, with_relations=_RELATIONS)

