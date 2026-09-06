from datetime import datetime, timezone
import secrets
from uuid import uuid4

from app.application.dto.bookings.booking import BookingPaymentDTO
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


class CreateBookingPaymentUseCase(BaseUseCase):
    def __init__(
        self,
        booking_service: BookingService,
        payment_service: PaymentService,
        current_user: CurrentUser,
        event_bus: EventBus | None = None,
    ):
        self.booking_service = booking_service
        self.payment_service = payment_service
        self.current_user = current_user
        self.event_bus = event_bus or RedisEventBus()

    async def execute(self, booking_identifier: str, data: BookingPaymentDTO) -> Payment:
        if not settings.PAYMENT_ENABLED:
            raise AppException(
                status_code=400,
                message="Payment processing is currently disabled.",
                error_code="PAYMENT_DISABLED",
            )

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
                message="Cannot make payment for a cancelled booking.",
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

        amount_to_pay = round(data.amount, 2) if data.amount is not None else remaining_balance

        if amount_to_pay <= 0:
            raise AppException(
                status_code=400,
                message="Payment amount must be greater than zero.",
                error_code="INVALID_AMOUNT",
                field="amount",
            )

        if amount_to_pay > remaining_balance + 0.01:
            raise AppException(
                status_code=400,
                message=f"Payment amount ({amount_to_pay}) exceeds remaining balance ({remaining_balance}).",
                error_code="AMOUNT_EXCEEDS_BALANCE",
                field="amount",
            )

        # Map payment method enum safely
        payment_method_enum = None
        try:
            payment_method_enum = PaymentMethod(data.payment_method.lower())
        except (ValueError, KeyError):
            payment_method_enum = PaymentMethod.CARD

        transaction_id = data.transaction_id or f"TXN{datetime.now(timezone.utc).strftime('%y%m%d')}{secrets.token_hex(4).upper()}"

        payment = Payment(
            booking_id=booking.id,
            amount=amount_to_pay,
            currency=booking.currency or "INR",
            payment_method=payment_method_enum,
            gateway=data.gateway or "internal",
            transaction_id=transaction_id,
            status=TransactionStatus.SUCCESS,
            paid_at=datetime.now(timezone.utc),
        )

        created_payment = await self.payment_service.create(payment)

        # Update booking payment and booking status
        new_total_paid = total_paid_so_far + amount_to_pay
        booking_just_completed = False
        if new_total_paid >= float(booking.total_amount) - 0.01:
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
            with_relations={"guest": True, "property": True, "room_type": True} if booking_just_completed else None,
        )

        # Publish event so the email + PDF handler fires asynchronously
        if booking_just_completed:
            event = BookingCompletedEvent(updated_booking)
            await self.event_bus.publish(event)

        return created_payment

