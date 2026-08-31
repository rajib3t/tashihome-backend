from app.application.dto.payouts.payout import AdminPayoutCreateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.payout_model import Payout, PayoutStatus
from app.services.payout_service import PayoutService
from app.services.user_service import UserService
from app.services.vendor_bank_account_service import VendorBankAccountService

_RELATIONS = {
    "vendor": True,
    "bank_account": True,
    "creator": True,
}


class CreatePayoutUseCase(BaseUseCase):
    def __init__(
        self,
        payout_service: PayoutService,
        user_service: UserService,
        vendor_bank_account_service: VendorBankAccountService,
        current_user: CurrentUser,
    ):
        self.payout_service = payout_service
        self.user_service = user_service
        self.vendor_bank_account_service = vendor_bank_account_service
        self.current_user = current_user

    async def execute(self, data: AdminPayoutCreateDTO) -> Payout:
        vendor = await self.user_service.get_user_by_public_id(data.vendor_id)
        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found.",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        bank_account_id = None
        if data.bank_account_id:
            bank_account = await self.vendor_bank_account_service.get_by_public_id(data.bank_account_id)
            if not bank_account or bank_account.vendor_id != vendor.id:
                raise AppException(
                    status_code=404,
                    message="Specified bank account not found for this vendor.",
                    error_code="BANK_ACCOUNT_NOT_FOUND",
                    field="bank_account_id",
                )
            bank_account_id = bank_account.id
        else:
            primary_account = await self.vendor_bank_account_service.get_primary_by_vendor_id(vendor.id)
            if primary_account:
                bank_account_id = primary_account.id

        if data.period_end < data.period_start:
            raise AppException(
                status_code=422,
                message="period_end must be greater than or equal to period_start.",
                error_code="INVALID_PERIOD",
                field="period_end",
            )

        payout = Payout(
            vendor_id=vendor.id,
            bank_account_id=bank_account_id,
            gross_amount=data.gross_amount,
            commission_amount=data.commission_amount or 0.0,
            amount=data.amount,
            currency=data.currency or "INR",
            period_start=data.period_start,
            period_end=data.period_end,
            status=PayoutStatus.PENDING,
            mode=data.mode or "NEFT",
            notes=data.notes,
            created_by=self.current_user.id,
        )

        return await self.payout_service.create(payout, with_relations=_RELATIONS)

