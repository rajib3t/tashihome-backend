import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.core.config import Settings, settings
from app.core.exceptions import AppException
from app.application.dto.bookings.booking import (
    BookingPaymentDTO,
    RazorpayCreateOrderDTO,
    RazorpayVerifyPaymentDTO,
)
from app.application.use_case.user.booking.create_booking_payment_use_case import (
    CreateBookingPaymentUseCase,
)
from app.application.use_case.user.booking.create_razorpay_order_use_case import (
    CreateRazorpayOrderUseCase,
)
from app.application.use_case.user.booking.verify_razorpay_payment_use_case import (
    VerifyRazorpayPaymentUseCase,
)
from app.application.use_case.admin.bookings.update_refund_request_use_case import (
    AdminProcessRefundUseCase,
)


def test_payment_enabled_settings():
    # Test setting model defaults and overrides
    custom_settings = Settings(
        APP_NAME="Test",
        DATABASE_URL="postgresql://test:test@localhost:5432/test",
        JWT_SECRET="secret",
        PAYMENT_ENABLED=False,
    )
    assert custom_settings.PAYMENT_ENABLED is False

    custom_settings_enabled = Settings(
        APP_NAME="Test",
        DATABASE_URL="postgresql://test:test@localhost:5432/test",
        JWT_SECRET="secret",
        PAYMENT_ENABLED=True,
    )
    assert custom_settings_enabled.PAYMENT_ENABLED is True


def test_create_razorpay_order_disabled_payment():
    async def run_test():
        orig = settings.PAYMENT_ENABLED
        try:
            settings.PAYMENT_ENABLED = False
            use_case = CreateRazorpayOrderUseCase(
                booking_service=AsyncMock(),
                razorpay_service=AsyncMock(),
                current_user=MagicMock(),
            )
            with pytest.raises(AppException) as exc_info:
                await use_case.execute("booking-id", RazorpayCreateOrderDTO(amount=100.0))

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail.get("error_code") == "PAYMENT_DISABLED"
            assert "Payment processing is currently disabled" in exc_info.value.detail.get("message")
        finally:
            settings.PAYMENT_ENABLED = orig

    asyncio.run(run_test())


def test_create_booking_payment_disabled_payment():
    async def run_test():
        orig = settings.PAYMENT_ENABLED
        try:
            settings.PAYMENT_ENABLED = False
            use_case = CreateBookingPaymentUseCase(
                booking_service=AsyncMock(),
                payment_service=AsyncMock(),
                current_user=MagicMock(),
            )
            dto = BookingPaymentDTO(payment_method="card", amount=100.0)
            with pytest.raises(AppException) as exc_info:
                await use_case.execute("booking-id", dto)

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail.get("error_code") == "PAYMENT_DISABLED"
            assert "Payment processing is currently disabled" in exc_info.value.detail.get("message")
        finally:
            settings.PAYMENT_ENABLED = orig

    asyncio.run(run_test())


def test_verify_razorpay_payment_disabled_payment():
    async def run_test():
        orig = settings.PAYMENT_ENABLED
        try:
            settings.PAYMENT_ENABLED = False
            use_case = VerifyRazorpayPaymentUseCase(
                booking_service=AsyncMock(),
                payment_service=AsyncMock(),
                razorpay_service=AsyncMock(),
                current_user=MagicMock(),
            )
            dto = RazorpayVerifyPaymentDTO(
                razorpay_order_id="order_123",
                razorpay_payment_id="pay_123",
                razorpay_signature="sig_123",
            )
            with pytest.raises(AppException) as exc_info:
                await use_case.execute("booking-id", dto)

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail.get("error_code") == "PAYMENT_DISABLED"
            assert "Payment processing is currently disabled" in exc_info.value.detail.get("message")
        finally:
            settings.PAYMENT_ENABLED = orig

    asyncio.run(run_test())


def test_admin_process_refund_disabled_payment():
    async def run_test():
        orig = settings.PAYMENT_ENABLED
        try:
            settings.PAYMENT_ENABLED = False
            use_case = AdminProcessRefundUseCase(
                refund_request_service=AsyncMock(),
                payment_service=AsyncMock(),
                razorpay_service=AsyncMock(),
                current_user=MagicMock(),
            )
            with pytest.raises(AppException) as exc_info:
                await use_case.execute("refund-id")

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail.get("error_code") == "PAYMENT_DISABLED"
            assert "Payment and refund processing is currently disabled" in exc_info.value.detail.get("message")
        finally:
            settings.PAYMENT_ENABLED = orig

    asyncio.run(run_test())

