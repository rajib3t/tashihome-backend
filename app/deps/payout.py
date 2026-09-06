from fastapi import Depends

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
    CreateVendorRazorpayContactUseCase,
    DeleteVendorBankAccountUseCase,
    ListVendorBankAccountsUseCase,
    SetPrimaryVendorBankAccountUseCase,
)
from app.application.use_case.admin.payouts.process_razorpay_payout_use_case import (
    ProcessRazorpayPayoutUseCase,
)
from app.application.use_case.admin.payouts.sync_razorpay_payout_use_case import (
    SyncRazorpayPayoutUseCase,
)
from app.deps.auth import CurrentUser, require_admin
from app.deps.service import (
    get_payout_service,
    get_razorpay_service,
    get_user_service,
    get_vendor_bank_account_service,
    get_vendor_razorpay_contact_service,
    get_vendor_razorpay_fund_account_service,
)
from app.services.payout_service import PayoutService
from app.services.razorpay_service import RazorpayService
from app.services.user_service import UserService
from app.services.vendor_bank_account_service import VendorBankAccountService
from app.services.vendor_razorpay_contact_service import VendorRazorpayContactService
from app.services.vendor_razorpay_fund_account_service import VendorRazorpayFundAccountService


async def get_list_payouts_use_case(
    payout_service: PayoutService = Depends(get_payout_service),
    user_service: UserService = Depends(get_user_service),
    _: CurrentUser = Depends(require_admin),
) -> ListPayoutsUseCase:
    return ListPayoutsUseCase(payout_service, user_service)


async def get_get_payout_use_case(
    payout_service: PayoutService = Depends(get_payout_service),
    _: CurrentUser = Depends(require_admin),
) -> GetPayoutUseCase:
    return GetPayoutUseCase(payout_service)


async def get_create_payout_use_case(
    payout_service: PayoutService = Depends(get_payout_service),
    user_service: UserService = Depends(get_user_service),
    vendor_bank_account_service: VendorBankAccountService = Depends(get_vendor_bank_account_service),
    current_user: CurrentUser = Depends(require_admin),
) -> CreatePayoutUseCase:
    return CreatePayoutUseCase(
        payout_service=payout_service,
        user_service=user_service,
        vendor_bank_account_service=vendor_bank_account_service,
        current_user=current_user,
    )


async def get_calculate_vendor_earnings_use_case(
    payout_service: PayoutService = Depends(get_payout_service),
    user_service: UserService = Depends(get_user_service),
    _: CurrentUser = Depends(require_admin),
) -> CalculateVendorEarningsUseCase:
    return CalculateVendorEarningsUseCase(payout_service, user_service)


async def get_process_razorpay_payout_use_case(
    payout_service: PayoutService = Depends(get_payout_service),
    user_service: UserService = Depends(get_user_service),
    vendor_bank_account_service: VendorBankAccountService = Depends(get_vendor_bank_account_service),
    vendor_razorpay_contact_service: VendorRazorpayContactService = Depends(get_vendor_razorpay_contact_service),
    vendor_razorpay_fund_account_service: VendorRazorpayFundAccountService = Depends(get_vendor_razorpay_fund_account_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    current_user: CurrentUser = Depends(require_admin),
) -> ProcessRazorpayPayoutUseCase:
    return ProcessRazorpayPayoutUseCase(
        payout_service=payout_service,
        user_service=user_service,
        vendor_bank_account_service=vendor_bank_account_service,
        vendor_razorpay_contact_service=vendor_razorpay_contact_service,
        vendor_razorpay_fund_account_service=vendor_razorpay_fund_account_service,
        razorpay_service=razorpay_service,
        current_user=current_user,
    )


async def get_sync_razorpay_payout_use_case(
    payout_service: PayoutService = Depends(get_payout_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    _: CurrentUser = Depends(require_admin),
) -> SyncRazorpayPayoutUseCase:
    return SyncRazorpayPayoutUseCase(payout_service, razorpay_service)


async def get_cancel_payout_use_case(
    payout_service: PayoutService = Depends(get_payout_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    _: CurrentUser = Depends(require_admin),
) -> CancelPayoutUseCase:
    return CancelPayoutUseCase(payout_service, razorpay_service)


async def get_list_vendor_bank_accounts_use_case(
    vendor_bank_account_service: VendorBankAccountService = Depends(get_vendor_bank_account_service),
    user_service: UserService = Depends(get_user_service),
    _: CurrentUser = Depends(require_admin),
) -> ListVendorBankAccountsUseCase:
    return ListVendorBankAccountsUseCase(vendor_bank_account_service, user_service)


async def get_create_vendor_bank_account_use_case(
    vendor_bank_account_service: VendorBankAccountService = Depends(get_vendor_bank_account_service),
    vendor_razorpay_contact_service: VendorRazorpayContactService = Depends(get_vendor_razorpay_contact_service),
    vendor_razorpay_fund_account_service: VendorRazorpayFundAccountService = Depends(get_vendor_razorpay_fund_account_service),
    user_service: UserService = Depends(get_user_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    _: CurrentUser = Depends(require_admin),
) -> CreateVendorBankAccountUseCase:
    return CreateVendorBankAccountUseCase(
        vendor_bank_account_service=vendor_bank_account_service,
        vendor_razorpay_contact_service=vendor_razorpay_contact_service,
        vendor_razorpay_fund_account_service=vendor_razorpay_fund_account_service,
        user_service=user_service,
        razorpay_service=razorpay_service,
    )


async def get_create_vendor_razorpay_contact_use_case(
    vendor_razorpay_contact_service: VendorRazorpayContactService = Depends(get_vendor_razorpay_contact_service),
    user_service: UserService = Depends(get_user_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    _: CurrentUser = Depends(require_admin),
) -> CreateVendorRazorpayContactUseCase:
    return CreateVendorRazorpayContactUseCase(
        vendor_razorpay_contact_service=vendor_razorpay_contact_service,
        user_service=user_service,
        razorpay_service=razorpay_service,
    )



async def get_set_primary_vendor_bank_account_use_case(
    vendor_bank_account_service: VendorBankAccountService = Depends(get_vendor_bank_account_service),
    user_service: UserService = Depends(get_user_service),
    _: CurrentUser = Depends(require_admin),
) -> SetPrimaryVendorBankAccountUseCase:
    return SetPrimaryVendorBankAccountUseCase(vendor_bank_account_service, user_service)


async def get_delete_vendor_bank_account_use_case(
    vendor_bank_account_service: VendorBankAccountService = Depends(get_vendor_bank_account_service),
    user_service: UserService = Depends(get_user_service),
    _: CurrentUser = Depends(require_admin),
) -> DeleteVendorBankAccountUseCase:
    return DeleteVendorBankAccountUseCase(vendor_bank_account_service, user_service)

