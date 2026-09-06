from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
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
from app.deps.payout import (
    get_calculate_vendor_earnings_use_case,
    get_cancel_payout_use_case,
    get_create_payout_use_case,
    get_create_vendor_bank_account_use_case,
    get_create_vendor_razorpay_contact_use_case,
    get_delete_vendor_bank_account_use_case,
    get_get_payout_use_case,
    get_list_payouts_use_case,
    get_list_vendor_bank_accounts_use_case,
    get_process_razorpay_payout_use_case,
    get_set_primary_vendor_bank_account_use_case,
    get_sync_razorpay_payout_use_case,
)
from app.schemas.payout_schema import (
    PayoutListResponseSchema,
    PayoutResponseSchema,
    ProcessPayoutResponseSchema,
    RazorpayContactResponseSchema,
    VendorBankAccountListResponseSchema,
    VendorBankAccountResponseSchema,
    VendorEarningsSummaryResponseSchema,
)
from app.schemas.response import BaseResponse
from app.utils.exception_decorate import handle_api_exceptions


class AdminPayoutController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/payouts",
            tags=["Admin - Payouts"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._list_payouts, {"response_model": PayoutListResponseSchema}),
            ("post", "/", self._create_payout, {"response_model": PayoutResponseSchema, "status_code": 201}),
            ("get", "/eligible", self._calculate_vendor_earnings, {"response_model": VendorEarningsSummaryResponseSchema}),
            ("get", "/{payout_id}", self._get_payout, {"response_model": PayoutResponseSchema}),
            ("post", "/{payout_id}/process", self._process_payout, {"response_model": ProcessPayoutResponseSchema}),
            ("post", "/{payout_id}/sync", self._sync_payout, {"response_model": PayoutResponseSchema}),
            ("post", "/{payout_id}/cancel", self._cancel_payout, {"response_model": PayoutResponseSchema}),
            ("get", "/vendors/{vendor_id}/bank-accounts", self._list_vendor_bank_accounts, {"response_model": VendorBankAccountListResponseSchema}),
            ("post", "/vendors/{vendor_id}/bank-accounts", self._create_vendor_bank_account, {"response_model": VendorBankAccountResponseSchema, "status_code": 201}),
            ("post", "/vendors/{vendor_id}/razorpay-contact", self._create_vendor_razorpay_contact, {"response_model": RazorpayContactResponseSchema, "status_code": 201}),
            ("patch", "/vendors/{vendor_id}/bank-accounts/{bank_account_id}/primary", self._set_primary_vendor_bank_account, {"response_model": VendorBankAccountResponseSchema}),
            ("delete", "/vendors/{vendor_id}/bank-accounts/{bank_account_id}", self._delete_vendor_bank_account, {"response_model": BaseResponse}),
        ]
        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)

    @handle_api_exceptions
    async def _list_payouts(
        self,
        params: AdminPayoutQueryDTO = Depends(),
        use_case: ListPayoutsUseCase = Depends(get_list_payouts_use_case),
    ):
        page = await use_case.execute(params)
        return self.build_response(
            message="Payouts retrieved successfully.",
            data=page.items,
            meta=self.pagination_meta(page),
        )

    @handle_api_exceptions
    async def _get_payout(
        self,
        payout_id: str,
        use_case: GetPayoutUseCase = Depends(get_get_payout_use_case),
    ):
        payout = await use_case.execute(payout_id)
        return self.build_response(
            message="Payout retrieved successfully.",
            data=payout,
        )

    @handle_api_exceptions
    async def _calculate_vendor_earnings(
        self,
        params: CalculateVendorEarningsDTO = Depends(),
        use_case: CalculateVendorEarningsUseCase = Depends(get_calculate_vendor_earnings_use_case),
    ):
        summary = await use_case.execute(params)
        return self.build_response(
            message="Vendor earnings summary calculated successfully.",
            data=summary,
        )

    @handle_api_exceptions
    async def _create_payout(
        self,
        data: AdminPayoutCreateDTO,
        use_case: CreatePayoutUseCase = Depends(get_create_payout_use_case),
    ):
        payout = await use_case.execute(data)
        return self.build_response(
            message="Payout created successfully.",
            data=payout,
        )

    @handle_api_exceptions
    async def _process_payout(
        self,
        payout_id: str,
        data: AdminPayoutProcessDTO = None,
        use_case: ProcessRazorpayPayoutUseCase = Depends(get_process_razorpay_payout_use_case),
    ):
        payout = await use_case.execute(payout_id, data)
        return self.build_response(
            message="Payout submitted to Razorpay successfully.",
            data=payout,
        )

    @handle_api_exceptions
    async def _sync_payout(
        self,
        payout_id: str,
        use_case: SyncRazorpayPayoutUseCase = Depends(get_sync_razorpay_payout_use_case),
    ):
        payout = await use_case.execute(payout_id)
        return self.build_response(
            message="Payout status synced from Razorpay successfully.",
            data=payout,
        )

    @handle_api_exceptions
    async def _cancel_payout(
        self,
        payout_id: str,
        use_case: CancelPayoutUseCase = Depends(get_cancel_payout_use_case),
    ):
        payout = await use_case.execute(payout_id)
        return self.build_response(
            message="Payout cancelled successfully.",
            data=payout,
        )

    @handle_api_exceptions
    async def _list_vendor_bank_accounts(
        self,
        vendor_id: str,
        use_case: ListVendorBankAccountsUseCase = Depends(get_list_vendor_bank_accounts_use_case),
    ):
        accounts = await use_case.execute(vendor_id)
        return self.build_response(
            message="Vendor bank accounts retrieved successfully.",
            data=accounts,
        )

    @handle_api_exceptions
    async def _create_vendor_bank_account(
        self,
        vendor_id: str,
        data: VendorBankAccountCreateDTO,
        use_case: CreateVendorBankAccountUseCase = Depends(get_create_vendor_bank_account_use_case),
    ):
        account = await use_case.execute(vendor_id, data)
        return self.build_response(
            message="Vendor bank account added successfully.",
            data=account,
        )

    @handle_api_exceptions
    async def _create_vendor_razorpay_contact(
        self,
        vendor_id: str,
        use_case: CreateVendorRazorpayContactUseCase = Depends(get_create_vendor_razorpay_contact_use_case),
    ):
        contact = await use_case.execute(vendor_id)
        return self.build_response(
            message="Vendor Razorpay contact processed successfully.",
            data=contact,
        )

    @handle_api_exceptions
    async def _set_primary_vendor_bank_account(
        self,
        vendor_id: str,
        bank_account_id: str,
        use_case: SetPrimaryVendorBankAccountUseCase = Depends(get_set_primary_vendor_bank_account_use_case),
    ):
        account = await use_case.execute(vendor_id, bank_account_id)
        return self.build_response(
            message="Vendor primary bank account updated successfully.",
            data=account,
        )

    @handle_api_exceptions
    async def _delete_vendor_bank_account(
        self,
        vendor_id: str,
        bank_account_id: str,
        use_case: DeleteVendorBankAccountUseCase = Depends(get_delete_vendor_bank_account_use_case),
    ):
        await use_case.execute(vendor_id, bank_account_id)
        return self.build_response(
            message="Vendor bank account removed successfully.",
            data={},
        )


controller = AdminPayoutController()
router = controller.router

