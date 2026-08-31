from typing import List

from app.application.dto.payouts.payout import (
    VendorBankAccountCreateDTO,
    VendorBankAccountUpdateDTO,
)
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.vendor_bank_account_model import BankAccountType, VendorBankAccount
from app.services.razorpay_service import RazorpayService
from app.services.user_service import UserService
from app.services.vendor_bank_account_service import VendorBankAccountService


class ListVendorBankAccountsUseCase(BaseUseCase):
    def __init__(
        self,
        vendor_bank_account_service: VendorBankAccountService,
        user_service: UserService,
    ):
        self.vendor_bank_account_service = vendor_bank_account_service
        self.user_service = user_service

    async def execute(self, vendor_id: str) -> List[VendorBankAccount]:
        vendor = await self.user_service.get_user_by_public_id(vendor_id)
        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found.",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )
        return await self.vendor_bank_account_service.list_by_vendor_id(vendor.id)


class CreateVendorBankAccountUseCase(BaseUseCase):
    def __init__(
        self,
        vendor_bank_account_service: VendorBankAccountService,
        user_service: UserService,
        razorpay_service: RazorpayService,
    ):
        self.vendor_bank_account_service = vendor_bank_account_service
        self.user_service = user_service
        self.razorpay_service = razorpay_service

    async def execute(self, vendor_id: str, data: VendorBankAccountCreateDTO) -> VendorBankAccount:
        vendor = await self.user_service.get_user_by_public_id(vendor_id)
        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found.",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        account_type = BankAccountType(data.account_type)
        if account_type == BankAccountType.BANK_ACCOUNT:
            if not data.account_number or not data.ifsc_code:
                raise AppException(
                    status_code=422,
                    message="account_number and ifsc_code are required for bank_account type.",
                    error_code="BANK_DETAILS_REQUIRED",
                    field="account_number",
                )
        elif account_type == BankAccountType.VPA:
            if not data.upi_id:
                raise AppException(
                    status_code=422,
                    message="upi_id is required for vpa type.",
                    error_code="UPI_ID_REQUIRED",
                    field="upi_id",
                )

        bank_account = VendorBankAccount(
            vendor_id=vendor.id,
            account_type=account_type,
            account_holder_name=data.account_holder_name,
            account_number=data.account_number,
            ifsc_code=data.ifsc_code.upper() if data.ifsc_code else None,
            bank_name=data.bank_name,
            branch_name=data.branch_name,
            upi_id=data.upi_id,
            is_primary=data.is_primary,
            is_verified=False,
            notes=data.notes,
        )

        # Attempt to create Razorpay Contact & Fund Account if Razorpay is configured
        if self.razorpay_service.is_configured():
            try:
                contact_res = await self.razorpay_service.create_contact(
                    name=vendor.full_name or data.account_holder_name,
                    email=vendor.email,
                    contact=vendor.phone,
                    type="vendor",
                    reference_id=str(vendor.public_id),
                )
                contact_id = contact_res.get("id")
                bank_account.razorpay_contact_id = contact_id

                if account_type == BankAccountType.VPA and data.upi_id:
                    fa_res = await self.razorpay_service.create_fund_account_vpa(
                        contact_id=contact_id,
                        vpa_address=data.upi_id,
                    )
                else:
                    fa_res = await self.razorpay_service.create_fund_account_bank(
                        contact_id=contact_id,
                        account_holder_name=data.account_holder_name,
                        account_number=data.account_number,
                        ifsc=data.ifsc_code,
                    )
                bank_account.razorpay_fund_account_id = fa_res.get("id")
                bank_account.is_verified = True
            except AppException:
                # If Razorpay call fails (e.g. invalid test keys/sandbox), we still save bank account locally for manual processing
                pass

        return await self.vendor_bank_account_service.create(bank_account)

