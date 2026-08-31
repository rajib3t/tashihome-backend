import asyncio
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.application.dto.payouts.payout import (
    AdminPayoutCreateDTO,
    AdminPayoutProcessDTO,
    AdminPayoutQueryDTO,
    CalculateVendorEarningsDTO,
    VendorBankAccountCreateDTO,
)
from app.application.use_case.admin.payouts.calculate_vendor_earnings_use_case import (
    CalculateVendorEarningsUseCase,
)
from app.application.use_case.admin.payouts.cancel_payout_use_case import (
    CancelPayoutUseCase,
)
from app.application.use_case.admin.payouts.create_payout_use_case import (
    CreatePayoutUseCase,
)
from app.application.use_case.admin.payouts.get_payout_use_case import (
    GetPayoutUseCase,
)
from app.application.use_case.admin.payouts.list_payouts_use_case import (
    ListPayoutsUseCase,
)
from app.application.use_case.admin.payouts.manage_vendor_bank_account_use_case import (
    CreateVendorBankAccountUseCase,
    ListVendorBankAccountsUseCase,
)
from app.application.use_case.admin.payouts.process_razorpay_payout_use_case import (
    ProcessRazorpayPayoutUseCase,
)
from app.application.use_case.admin.payouts.sync_razorpay_payout_use_case import (
    SyncRazorpayPayoutUseCase,
)
from app.core.config import settings
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.payout_model import Payout, PayoutStatus
from app.models.vendor_bank_account_model import BankAccountType, VendorBankAccount
from app.repositories.base_repository import Page


def test_list_payouts_use_case():
    async def run_test():
        payout_service = AsyncMock()
        user_service = AsyncMock()

        vendor_public_id = str(uuid.uuid4())
        mock_vendor = MagicMock()
        mock_vendor.id = 10
        user_service.get_user_by_public_id.return_value = mock_vendor

        expected_page = Page(items=[], total=0, page=1, page_size=10)
        payout_service.list_all.return_value = expected_page

        use_case = ListPayoutsUseCase(payout_service, user_service)
        query = AdminPayoutQueryDTO(vendor_id=vendor_public_id, page=1, size=10)

        result = await use_case.execute(query)
        assert result == expected_page
        payout_service.list_all.assert_called_once()

    asyncio.run(run_test())


def test_get_payout_use_case_found():
    async def run_test():
        payout_service = AsyncMock()
        mock_payout = MagicMock(spec=Payout)
        payout_service.get_by_public_id.return_value = mock_payout

        use_case = GetPayoutUseCase(payout_service)
        result = await use_case.execute("payout-uuid")
        assert result == mock_payout

    asyncio.run(run_test())


def test_get_payout_use_case_not_found():
    async def run_test():
        payout_service = AsyncMock()
        payout_service.get_by_public_id.return_value = None

        use_case = GetPayoutUseCase(payout_service)
        with pytest.raises(AppException) as exc_info:
            await use_case.execute("invalid-uuid")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail.get("error_code") == "PAYOUT_NOT_FOUND"

    asyncio.run(run_test())


def test_calculate_vendor_earnings_use_case():
    async def run_test():
        payout_service = AsyncMock()
        user_service = AsyncMock()

        mock_vendor = MagicMock()
        mock_vendor.id = 5
        mock_vendor.public_id = uuid.uuid4()
        mock_vendor.full_name = "Test Vendor"
        mock_vendor.email = "vendor@test.com"
        user_service.get_user_by_public_id.return_value = mock_vendor

        payout_service.calculate_vendor_earnings.return_value = {
            "vendor_id": 5,
            "period_start": date(2026, 8, 1),
            "period_end": date(2026, 8, 31),
            "completed_bookings_count": 10,
            "gross_booking_amount": 50000.0,
            "commission_percentage": 10.0,
            "commission_amount": 5000.0,
            "net_earned_amount": 45000.0,
            "already_disbursed_amount": 0.0,
            "pending_payable_amount": 45000.0,
        }

        use_case = CalculateVendorEarningsUseCase(payout_service, user_service)
        dto = CalculateVendorEarningsDTO(
            vendor_id=str(mock_vendor.public_id),
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
        )

        result = await use_case.execute(dto)
        assert result["pending_payable_amount"] == 45000.0
        assert result["vendor_email"] == "vendor@test.com"

    asyncio.run(run_test())


def test_create_payout_use_case():
    async def run_test():
        payout_service = AsyncMock()
        user_service = AsyncMock()
        bank_service = AsyncMock()
        current_user = CurrentUser(id=1, role="admin")

        mock_vendor = MagicMock()
        mock_vendor.id = 5
        user_service.get_user_by_public_id.return_value = mock_vendor

        mock_bank = MagicMock()
        mock_bank.id = 2
        bank_service.get_primary_by_vendor_id.return_value = mock_bank

        created_payout = MagicMock(spec=Payout)
        payout_service.create.return_value = created_payout

        use_case = CreatePayoutUseCase(
            payout_service=payout_service,
            user_service=user_service,
            vendor_bank_account_service=bank_service,
            current_user=current_user,
        )

        dto = AdminPayoutCreateDTO(
            vendor_id=str(uuid.uuid4()),
            gross_amount=10000.0,
            commission_amount=1000.0,
            amount=9000.0,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 15),
            mode="NEFT",
        )

        result = await use_case.execute(dto)
        assert result == created_payout
        payout_service.create.assert_called_once()

    asyncio.run(run_test())


def test_process_razorpay_payout_success():
    async def run_test():
        payout_service = AsyncMock()
        user_service = AsyncMock()
        bank_service = AsyncMock()
        razorpay_service = AsyncMock()
        current_user = CurrentUser(id=1, role="admin")

        mock_vendor = MagicMock()
        mock_vendor.id = 5
        mock_vendor.email = "vendor@test.com"
        mock_vendor.phone = "9876543210"
        mock_vendor.full_name = "Host Vendor"
        mock_vendor.public_id = uuid.uuid4()

        mock_bank = MagicMock(spec=VendorBankAccount)
        mock_bank.id = 2
        mock_bank.account_type = BankAccountType.BANK_ACCOUNT
        mock_bank.account_holder_name = "Host Vendor"
        mock_bank.account_number = "1234567890"
        mock_bank.ifsc_code = "HDFC0001234"
        mock_bank.razorpay_contact_id = "cont_123"
        mock_bank.razorpay_fund_account_id = "fa_123"

        mock_payout = MagicMock(spec=Payout)
        mock_payout.id = 1
        mock_payout.public_id = uuid.uuid4()
        mock_payout.vendor_id = 5
        mock_payout.vendor = mock_vendor
        mock_payout.bank_account = mock_bank
        mock_payout.status = PayoutStatus.PENDING
        mock_payout.amount = 5000.0
        mock_payout.currency = "INR"
        mock_payout.mode = "NEFT"

        payout_service.get_by_public_id.return_value = mock_payout
        payout_service.update.side_effect = lambda p, **kw: p

        razorpay_service.create_payout.return_value = {
            "id": "pout_12345",
            "status": "processed",
            "utr": "UTR999888777",
            "amount": 500000,
        }

        use_case = ProcessRazorpayPayoutUseCase(
            payout_service=payout_service,
            user_service=user_service,
            vendor_bank_account_service=bank_service,
            razorpay_service=razorpay_service,
            current_user=current_user,
        )

        result = await use_case.execute(str(mock_payout.public_id), AdminPayoutProcessDTO(mode="NEFT"))
        assert result.status == PayoutStatus.PAID
        assert result.razorpay_payout_id == "pout_12345"
        assert result.utr == "UTR999888777"
        razorpay_service.create_payout.assert_called_once()

    asyncio.run(run_test())


def test_process_razorpay_payout_payment_disabled():
    async def run_test():
        orig = settings.PAYMENT_ENABLED
        try:
            settings.PAYMENT_ENABLED = False
            use_case = ProcessRazorpayPayoutUseCase(
                payout_service=AsyncMock(),
                user_service=AsyncMock(),
                vendor_bank_account_service=AsyncMock(),
                razorpay_service=AsyncMock(),
                current_user=CurrentUser(id=1, role="admin"),
            )
            with pytest.raises(AppException) as exc_info:
                await use_case.execute("some-id")

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail.get("error_code") == "PAYMENT_DISABLED"
        finally:
            settings.PAYMENT_ENABLED = orig

    asyncio.run(run_test())


def test_sync_razorpay_payout_use_case():
    async def run_test():
        payout_service = AsyncMock()
        razorpay_service = AsyncMock()

        mock_payout = MagicMock(spec=Payout)
        mock_payout.razorpay_payout_id = "pout_123"
        mock_payout.status = PayoutStatus.PROCESSING
        mock_payout.utr = None
        mock_payout.paid_at = None

        payout_service.get_by_public_id.return_value = mock_payout
        payout_service.update.side_effect = lambda p, **kw: p

        razorpay_service.fetch_payout.return_value = {
            "id": "pout_123",
            "status": "processed",
            "utr": "UTR11223344",
        }

        use_case = SyncRazorpayPayoutUseCase(payout_service, razorpay_service)
        result = await use_case.execute("payout-id")

        assert result.status == PayoutStatus.PAID
        assert result.utr == "UTR11223344"

    asyncio.run(run_test())


def test_cancel_payout_use_case():
    async def run_test():
        payout_service = AsyncMock()
        razorpay_service = AsyncMock()

        mock_payout = MagicMock(spec=Payout)
        mock_payout.razorpay_payout_id = None
        mock_payout.status = PayoutStatus.PENDING

        payout_service.get_by_public_id.return_value = mock_payout
        payout_service.update.side_effect = lambda p, **kw: p

        use_case = CancelPayoutUseCase(payout_service, razorpay_service)
        result = await use_case.execute("payout-id")

        assert result.status == PayoutStatus.CANCELLED

    asyncio.run(run_test())


def test_create_vendor_bank_account_use_case():
    async def run_test():
        bank_service = AsyncMock()
        user_service = AsyncMock()
        razorpay_service = AsyncMock()

        mock_vendor = MagicMock()
        mock_vendor.id = 12
        mock_vendor.email = "v@example.com"
        mock_vendor.phone = "9999999999"
        mock_vendor.full_name = "Host"
        mock_vendor.public_id = uuid.uuid4()
        user_service.get_user_by_public_id.return_value = mock_vendor

        razorpay_service.is_configured.return_value = True
        razorpay_service.create_contact.return_value = {"id": "cont_abc"}
        razorpay_service.create_fund_account_bank.return_value = {"id": "fa_abc"}

        bank_service.create.side_effect = lambda a: a

        use_case = CreateVendorBankAccountUseCase(bank_service, user_service, razorpay_service)
        dto = VendorBankAccountCreateDTO(
            account_type="bank_account",
            account_holder_name="Host",
            account_number="12345678",
            ifsc_code="SBIN0001234",
            bank_name="State Bank of India",
        )

        result = await use_case.execute(str(mock_vendor.public_id), dto)
        assert result.vendor_id == 12
        assert result.razorpay_contact_id == "cont_abc"
        assert result.razorpay_fund_account_id == "fa_abc"
        assert result.is_verified is True

    asyncio.run(run_test())

