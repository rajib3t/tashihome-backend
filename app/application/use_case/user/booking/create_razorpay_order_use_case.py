from typing import Any, Dict

from app.application.dto.bookings.booking import RazorpayCreateOrderDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.config import settings
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.booking_model import BookingStatus, PaymentStatus
from app.models.payment_model import TransactionStatus
from app.services.booking_service import BookingService
from app.services.razorpay_service import RazorpayService


class CreateRazorpayOrderUseCase(BaseUseCase):
    def __init__(
        self,
        booking_service: BookingService,
        razorpay_service: RazorpayService,
        current_user: CurrentUser,
    ):
        self.booking_service = booking_service
        self.razorpay_service = razorpay_service
        self.current_user = current_user

    async def execute(self, booking_identifier: str, data: RazorpayCreateOrderDTO) -> Dict[str, Any]:
        booking = await self.booking_service.get_user_booking_by_identifier(
            guest_id=self.current_user.id,
            identifier=booking_identifier,
            with_relations={"payments": True},
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
                message="Cannot create payment order for a cancelled booking.",
                error_code="BOOKING_CANCELLED",
            )

        if booking.payment_status == PaymentStatus.PAID:
            raise AppException(
                status_code=400,
                message="Booking is already fully paid.",
                error_code="ALREADY_PAID",
            )

        # Calculate remaining balance
        successful_payments = [
            p for p in (booking.payments or []) if p.status == TransactionStatus.SUCCESS
        ]
        total_paid_so_far = sum(float(p.amount) for p in successful_payments)
        remaining_balance = round(float(booking.total_amount) - total_paid_so_far, 2)

        order_amount = round(data.amount, 2) if data.amount is not None else remaining_balance

        if order_amount <= 0:
            raise AppException(
                status_code=400,
                message="Payment amount must be greater than zero.",
                error_code="INVALID_AMOUNT",
                field="amount",
            )

        if order_amount > remaining_balance + 0.01:
            raise AppException(
                status_code=400,
                message=f"Order amount ({order_amount}) exceeds remaining balance ({remaining_balance}).",
                error_code="AMOUNT_EXCEEDS_BALANCE",
                field="amount",
            )

        # Create Razorpay Order
        razorpay_order = await self.razorpay_service.create_order(
            amount=order_amount,
            currency=booking.currency or "INR",
            receipt=booking.booking_reference,
            notes={
                "booking_id": str(booking.public_id),
                "booking_reference": booking.booking_reference,
                "guest_id": str(self.current_user.id),
            },
        )

        return {
            "order_id": razorpay_order["id"],
            "amount": order_amount,
            "amount_in_paise": razorpay_order["amount"],
            "currency": razorpay_order.get("currency", "INR"),
            "key_id": settings.RAZORPAY_KEY_ID or "",
            "booking_id": str(booking.public_id),
            "booking_reference": booking.booking_reference,
        }

