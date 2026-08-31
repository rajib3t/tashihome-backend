from datetime import datetime, timezone

from app.application.dto.bookings.booking import RazorpayVerifyPaymentDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.config import settings
from app.core.events import EventBus, RedisEventBus
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.events.events.bookings.booking_completed_event import BookingCompletedEvent
from app.models.booking_model import BookingStatus, PaymentStatus
from app.models.payment_model import Payment, PaymentMethod, TransactionStatus
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.razorpay_service import RazorpayService


class VerifyRazorpayPaymentUseCase(BaseUseCase):
    def __init__(
        self,
        booking_service: BookingService,
        payment_service: PaymentService,
        razorpay_service: RazorpayService,
        current_user: CurrentUser,
        event_bus: EventBus | None = None,
    ):
        self.booking_service = booking_service
        self.payment_service = payment_service
        self.razorpay_service = razorpay_service
        self.current_user = current_user
        self.event_bus = event_bus or RedisEventBus()

    async def execute(self, booking_identifier: str, data: RazorpayVerifyPaymentDTO) -> Payment:
        if not settings.PAYMENT_ENABLED:
            raise AppException(
                status_code=400,
                message="Payment processing is currently disabled.",
                error_code="PAYMENT_DISABLED",
            )

        # 1. Verify HMAC Signature
        is_valid = self.razorpay_service.verify_payment_signature(
            razorpay_order_id=data.razorpay_order_id,
            razorpay_payment_id=data.razorpay_payment_id,
            razorpay_signature=data.razorpay_signature,
        )

        if not is_valid:
            raise AppException(
                status_code=400,
                message="Invalid Razorpay payment signature.",
                error_code="INVALID_PAYMENT_SIGNATURE",
            )

        # 2. Fetch Booking
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

        # Check if transaction already recorded to prevent duplicate credits
        existing_payment = await self.payment_service.get_by_transaction_id(data.razorpay_payment_id)
        if existing_payment:
            return existing_payment

        # 3. Fetch payment details from Razorpay to get exact captured amount and method
        paid_amount = 0.0
        payment_method_enum = PaymentMethod.CARD
        try:
            rzp_payment = await self.razorpay_service.fetch_payment(data.razorpay_payment_id)
            amount_in_paise = rzp_payment.get("amount", 0)
            paid_amount = round(amount_in_paise / 100.0, 2)
            method_str = rzp_payment.get("method", "card").lower()
            if method_str in ["card", "upi", "netbanking", "wallet", "bank_transfer"]:
                payment_method_enum = PaymentMethod(method_str)
        except Exception:
            # Fallback if fetch fails but signature was valid
            successful_payments = [
                p for p in (booking.payments or []) if p.status == TransactionStatus.SUCCESS
            ]
            total_paid_so_far = sum(float(p.amount) for p in successful_payments)
            paid_amount = max(0.0, round(float(booking.total_amount) - total_paid_so_far, 2))

        # 4. Create Payment Record
        payment = Payment(
            booking_id=booking.id,
            amount=paid_amount,
            currency=booking.currency or "INR",
            payment_method=payment_method_enum,
            gateway="razorpay",
            transaction_id=data.razorpay_payment_id,
            status=TransactionStatus.SUCCESS,
            paid_at=datetime.now(timezone.utc),
        )
        created_payment = await self.payment_service.create(payment)

        # 5. Update Booking Status
        successful_payments = [
            p for p in (booking.payments or []) if p.status == TransactionStatus.SUCCESS
        ]
        total_paid_so_far = sum(float(p.amount) for p in successful_payments) + paid_amount

        booking_just_completed = False
        if total_paid_so_far >= float(booking.total_amount) - 0.01:
            booking.payment_status = PaymentStatus.PAID
            if booking.status == BookingStatus.PENDING:
                booking.status = BookingStatus.CONFIRMED
            # Generate invoice number if not already set
            if not booking.invoice_number:
                booking.invoice_number = await self.booking_service.generate_invoice_number()
                booking_just_completed = True
        else:
            booking.payment_status = PaymentStatus.PARTIALLY_PAID

        booking.updated_by = self.current_user.id
        updated_booking = await self.booking_service.update_booking(
            booking,
            with_relations={"guest": True, "property": True} if booking_just_completed else None,
        )

        # Publish event so the email + PDF handler fires asynchronously
        if booking_just_completed:
            event = BookingCompletedEvent(updated_booking)
            await self.event_bus.publish(event)

        return created_payment

