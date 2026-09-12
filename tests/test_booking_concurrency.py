import asyncio
from datetime import date, datetime, timedelta, timezone
import unittest
from unittest.mock import AsyncMock, MagicMock
import uuid

from app.application.dto.bookings.booking import BookingCreateDTO, RazorpayCreateOrderDTO
from app.application.use_case.user.booking.create_booking_use_case import CreateBookingUseCase
from app.application.use_case.user.booking.create_razorpay_order_use_case import CreateRazorpayOrderUseCase
from app.application.use_case.user.booking.verify_razorpay_payment_use_case import VerifyRazorpayPaymentUseCase
from app.core.exceptions import AppException
from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.property_model import Property, PropertyStatus
from app.models.room_type_model import RoomType


class TestBookingConcurrencyAndLocking(unittest.TestCase):
    def setUp(self):
        self.user = MagicMock()
        self.user.id = 1
        self.user.role = "user"

    def test_create_booking_acquires_lock_and_succeeds(self):
        async def run_test():
            prop_uuid = str(uuid.uuid4())
            property_mock = MagicMock(spec=Property)
            property_mock.id = 10
            property_mock.public_id = prop_uuid
            property_mock.status = PropertyStatus.ACTIVE
            property_mock.property_room_types = []
            property_mock.cancellation_policy_id = 1
            property_mock.currency = "INR"

            booking_service = AsyncMock()
            booking_service.generate_booking_reference.return_value = "BK20260912TEST"
            booking_service.check_availability.return_value = {
                "is_available": True,
                "available_units": 1,
            }
            booking_service.calculate_pricing_quote.return_value = {
                "price_per_night": 2000.0,
                "discount_amount": 0.0,
                "tax_amount": 240.0,
                "total_amount": 2240.0,
                "currency": "INR",
            }
            
            created_booking = MagicMock(spec=Booking)
            booking_service.create_booking.return_value = created_booking

            property_service = AsyncMock()
            property_service.get_by_public_id.return_value = property_mock
            room_type_service = AsyncMock()

            use_case = CreateBookingUseCase(
                booking_service=booking_service,
                property_service=property_service,
                room_type_service=room_type_service,
                current_user=self.user,
            )

            dto = BookingCreateDTO(
                property_id=prop_uuid,
                check_in_date=date.today() + timedelta(days=2),
                check_out_date=date.today() + timedelta(days=4),
                num_rooms=1,
                num_guests=2,
            )

            result = await use_case.execute(dto)

            # Verify lock was acquired on property id before availability check
            booking_service.lock_property_for_booking.assert_awaited_once_with(10)
            booking_service.check_availability.assert_awaited_once()
            booking_service.create_booking.assert_awaited_once()

            # Verify expires_at was passed to Booking
            call_kwargs = booking_service.create_booking.call_args[1]
            booking_arg = call_kwargs["booking"]
            self.assertIsNotNone(booking_arg.expires_at)
            self.assertGreater(booking_arg.expires_at, datetime.now(timezone.utc))

        asyncio.run(run_test())

    def test_create_booking_fails_when_concurrent_booking_exhausts_units(self):
        async def run_test():
            prop_uuid = str(uuid.uuid4())
            property_mock = MagicMock(spec=Property)
            property_mock.id = 10
            property_mock.public_id = prop_uuid
            property_mock.status = PropertyStatus.ACTIVE
            property_mock.property_room_types = []

            booking_service = AsyncMock()
            # Simulate second concurrent request: after waiting on lock, 0 units left
            booking_service.check_availability.return_value = {
                "is_available": False,
                "available_units": 0,
            }

            property_service = AsyncMock()
            property_service.get_by_public_id.return_value = property_mock
            room_type_service = AsyncMock()

            use_case = CreateBookingUseCase(
                booking_service=booking_service,
                property_service=property_service,
                room_type_service=room_type_service,
                current_user=self.user,
            )

            dto = BookingCreateDTO(
                property_id=prop_uuid,
                check_in_date=date.today() + timedelta(days=2),
                check_out_date=date.today() + timedelta(days=4),
                num_rooms=1,
                num_guests=2,
            )

            with self.assertRaises(AppException) as ctx:
                await use_case.execute(dto)

            self.assertEqual(ctx.exception.status_code, 400)
            self.assertEqual(ctx.exception.detail.get("error_code"), "ROOMS_UNAVAILABLE")
            booking_service.lock_property_for_booking.assert_awaited_once_with(10)
            booking_service.create_booking.assert_not_called()

        asyncio.run(run_test())

    def test_create_razorpay_order_rejects_expired_pending_booking(self):
        async def run_test():
            booking_mock = MagicMock(spec=Booking)
            booking_mock.id = 100
            booking_mock.status = BookingStatus.PENDING
            booking_mock.payment_status = PaymentStatus.PENDING
            booking_mock.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
            booking_mock.payments = []

            booking_service = AsyncMock()
            booking_service.get_user_booking_by_identifier.return_value = booking_mock

            razorpay_service = AsyncMock()

            use_case = CreateRazorpayOrderUseCase(
                booking_service=booking_service,
                razorpay_service=razorpay_service,
                current_user=self.user,
            )

            dto = RazorpayCreateOrderDTO(amount=1000.0)

            with self.assertRaises(AppException) as ctx:
                await use_case.execute("BK12345", dto)

            self.assertEqual(ctx.exception.status_code, 400)
            self.assertEqual(ctx.exception.detail.get("error_code"), "BOOKING_EXPIRED")
            self.assertEqual(booking_mock.status, BookingStatus.CANCELLED)
            booking_service.update_booking.assert_awaited_once_with(booking_mock)
            razorpay_service.create_order.assert_not_called()

        asyncio.run(run_test())

    def test_verify_razorpay_payment_cancels_when_expired_and_rebooked(self):
        async def run_test():
            booking_mock = MagicMock(spec=Booking)
            booking_mock.id = 100
            booking_mock.booking_reference = "BK12345"
            booking_mock.status = BookingStatus.PENDING
            booking_mock.payment_status = PaymentStatus.PENDING
            booking_mock.total_amount = 2000.0
            booking_mock.currency = "INR"
            booking_mock.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
            booking_mock.payments = []
            booking_mock.property_id = 1
            booking_mock.room_type_id = None
            booking_mock.check_in_date = date.today() + timedelta(days=2)
            booking_mock.check_out_date = date.today() + timedelta(days=4)
            booking_mock.num_rooms = 1

            booking_service = AsyncMock()
            booking_service.get_user_booking_by_identifier.return_value = booking_mock
            # The room was already rebooked by someone else after expiry
            booking_service.check_availability.return_value = {"is_available": False, "available_units": 0}

            payment_service = AsyncMock()
            payment_service.get_by_transaction_id.return_value = None
            payment_service.create.return_value = MagicMock()

            razorpay_service = MagicMock()
            razorpay_service.verify_payment_signature.return_value = True
            razorpay_service.fetch_payment = AsyncMock(return_value={"amount": 200000, "method": "card"})

            use_case = VerifyRazorpayPaymentUseCase(
                booking_service=booking_service,
                payment_service=payment_service,
                razorpay_service=razorpay_service,
                current_user=self.user,
            )

            from app.application.dto.bookings.booking import RazorpayVerifyPaymentDTO
            dto = RazorpayVerifyPaymentDTO(
                razorpay_order_id="order_123",
                razorpay_payment_id="pay_123",
                razorpay_signature="sig_123",
            )

            await use_case.execute("BK12345", dto)

            # Must be cancelled because dates were rebooked
            self.assertEqual(booking_mock.status, BookingStatus.CANCELLED)
            self.assertIn("rebooked", booking_mock.cancellation_reason)
            booking_service.update_booking.assert_awaited_once()

        asyncio.run(run_test())

