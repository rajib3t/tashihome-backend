from datetime import datetime, timezone
from typing import Any, Dict

from app.application.dto.bookings.refund import AdminRefundStatusUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.refund_request_model import RefundRequest, RefundRequestStatus
from app.models.payment_model import TransactionStatus
from app.services.payment_service import PaymentService
from app.services.refund_request_service import RefundRequestService
from app.services.razorpay_service import RazorpayService


_RELATIONS = {
    "booking": True,
    "payment": True,
    "requester": True,
    "approver": True,
}


class AdminUpdateRefundStatusUseCase(BaseUseCase):
    """Approve or reject a refund request (no gateway call)."""

    def __init__(
        self,
        refund_request_service: RefundRequestService,
        current_user: CurrentUser,
    ):
        self.refund_request_service = refund_request_service
        self.current_user = current_user

    async def execute(
        self, refund_request_id: str, data: AdminRefundStatusUpdateDTO
    ) -> RefundRequest:
        refund_request = await self.refund_request_service.get_by_public_id(
            refund_request_id,
            with_relations=_RELATIONS,
        )
        if not refund_request:
            raise AppException(
                status_code=404,
                message="Refund request not found.",
                error_code="REFUND_REQUEST_NOT_FOUND",
                field="refund_request_id",
            )

        if refund_request.status == RefundRequestStatus.PROCESSED:
            raise AppException(
                status_code=400,
                message="Cannot update a refund request that has already been processed.",
                error_code="REFUND_ALREADY_PROCESSED",
            )

        new_status = RefundRequestStatus(data.status)
        refund_request.status = new_status
        refund_request.approved_by = self.current_user.id
        refund_request.approved_at = datetime.now(timezone.utc)

        return await self.refund_request_service.update(
            refund_request,
            with_relations=_RELATIONS,
        )


class AdminProcessRefundUseCase(BaseUseCase):
    """Process an approved refund via Razorpay and mark it as PROCESSED."""

    def __init__(
        self,
        refund_request_service: RefundRequestService,
        payment_service: PaymentService,
        razorpay_service: RazorpayService,
        current_user: CurrentUser,
    ):
        self.refund_request_service = refund_request_service
        self.payment_service = payment_service
        self.razorpay_service = razorpay_service
        self.current_user = current_user

    async def execute(self, refund_request_id: str) -> Dict[str, Any]:
        refund_request = await self.refund_request_service.get_by_public_id(
            refund_request_id,
            with_relations=_RELATIONS,
        )
        if not refund_request:
            raise AppException(
                status_code=404,
                message="Refund request not found.",
                error_code="REFUND_REQUEST_NOT_FOUND",
                field="refund_request_id",
            )

        if refund_request.status == RefundRequestStatus.PROCESSED:
            raise AppException(
                status_code=400,
                message="Refund has already been processed.",
                error_code="REFUND_ALREADY_PROCESSED",
            )

        if refund_request.status != RefundRequestStatus.APPROVED:
            raise AppException(
                status_code=400,
                message=f"Refund must be approved before processing. Current status: '{refund_request.status.value}'.",
                error_code="REFUND_NOT_APPROVED",
            )

        payment = await self.payment_service.get_by_id(refund_request.payment_id)
        if not payment:
            raise AppException(
                status_code=404,
                message="Associated payment not found.",
                error_code="PAYMENT_NOT_FOUND",
            )

        razorpay_refund_id = None
        razorpay_status = None

        # Attempt gateway refund if payment was made via Razorpay
        if payment.gateway == "razorpay" and payment.transaction_id:
            rzp_response = await self.razorpay_service.create_refund(
                payment_id=payment.transaction_id,
                amount=float(refund_request.amount),
                notes={"refund_request_id": str(refund_request.public_id)},
            )
            razorpay_refund_id = rzp_response.get("id")
            razorpay_status = rzp_response.get("status")

            # Update payment refunded amount and status
            payment.refunded_amount = float(payment.refunded_amount or 0) + float(refund_request.amount)
            if float(payment.refunded_amount) >= float(payment.amount):
                payment.status = TransactionStatus.REFUNDED
            else:
                payment.status = TransactionStatus.PARTIALLY_REFUNDED
            await self.payment_service.update(payment)

        # Mark refund request as processed
        refund_request.status = RefundRequestStatus.PROCESSED
        refund_request.approved_by = self.current_user.id
        refund_request.razorpay_refund_id = razorpay_refund_id
        refund_request.razorpay_status = razorpay_status
        if not refund_request.approved_at:
            refund_request.approved_at = datetime.now(timezone.utc)
        updated_refund = await self.refund_request_service.update(
            refund_request,
            with_relations=_RELATIONS,
        )

        return {
            "refund_request": updated_refund,
            "razorpay_refund_id": razorpay_refund_id,
            "razorpay_status": razorpay_status,
        }

