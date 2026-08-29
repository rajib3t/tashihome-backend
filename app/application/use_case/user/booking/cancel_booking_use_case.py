from datetime import datetime, timezone
from typing import Any, Dict

from app.application.dto.bookings.booking import BookingCancelDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.booking_model import BookingStatus
from app.models.payment_model import TransactionStatus
from app.models.refund_request_model import RefundRequest, RefundRequestStatus
from app.services.booking_service import BookingService
from app.services.refund_request_service import RefundRequestService


class CancelBookingUseCase(BaseUseCase):
    def __init__(
        self,
        booking_service: BookingService,
        refund_request_service: RefundRequestService,
        current_user: CurrentUser,
    ):
        self.booking_service = booking_service
        self.refund_request_service = refund_request_service
        self.current_user = current_user

    async def execute(self, booking_identifier: str, data: BookingCancelDTO) -> Dict[str, Any]:
        booking = await self.booking_service.get_user_booking_by_identifier(
            guest_id=self.current_user.id,
            identifier=booking_identifier,
            with_relations={
                "guest": True,
                "property": True,
                "room_type": True,
                "cancellation_policy": True,
                "payments": True,
                "refund_requests": True,
            },
        )

        if not booking:
            raise AppException(
                status_code=404,
                message="Booking not found.",
                error_code="BOOKING_NOT_FOUND",
                field="booking_id",
            )

        if booking.status == BookingStatus.CANCELLED:
            raise AppException(
                status_code=400,
                message="Booking is already cancelled.",
                error_code="BOOKING_ALREADY_CANCELLED",
            )

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise AppException(
                status_code=400,
                message=f"Cannot cancel booking with status '{booking.status.value}'.",
                error_code="CANNOT_CANCEL_BOOKING",
            )

        # Calculate successful payments
        successful_payments = [
            p for p in (booking.payments or []) if p.status == TransactionStatus.SUCCESS
        ]
        total_paid = sum(float(p.amount) for p in successful_payments)

        # Calculate refund based on policy
        refund_pct, refund_amount, policy_summary = (
            self.booking_service.calculate_cancellation_refund(booking, total_paid)
        )

        refund_req_id = None
        if refund_amount > 0 and successful_payments:
            primary_payment = successful_payments[0]
            refund_req = RefundRequest(
                payment_id=primary_payment.id,
                booking_id=booking.id,
                requested_by=self.current_user.id,
                reason=data.reason or "Guest requested cancellation",
                amount=refund_amount,
                status=RefundRequestStatus.PENDING,
            )
            created_refund_req = await self.refund_request_service.create(refund_req)
            refund_req_id = str(created_refund_req.public_id)

        # Update booking
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = data.reason
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.updated_by = self.current_user.id

        updated_booking = await self.booking_service.update_booking(
            booking=booking,
            with_relations={
                "guest": True,
                "property": True,
                "room_type": True,
                "cancellation_policy": True,
                "payments": True,
                "refund_requests": True,
                "review": True,
            },
        )

        return {
            "booking": updated_booking,
            "refund_percentage": refund_pct,
            "refund_amount": refund_amount,
            "policy_summary": policy_summary,
            "refund_request_id": refund_req_id,
        }

