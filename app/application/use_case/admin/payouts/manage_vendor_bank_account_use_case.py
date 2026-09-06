import json
from typing import List

from app.application.dto.payouts.payout import (
    VendorBankAccountCreateDTO,
    VendorBankAccountUpdateDTO,
)
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.vendor_bank_account_model import BankAccountType, VendorBankAccount
from app.models.vendor_razorpay_contact_model import VendorRazorpayContact
from app.models.vendor_razorpay_fund_account_model import VendorRazorpayFundAccount
from app.services.razorpay_service import RazorpayService
from app.services.user_service import UserService
from app.services.vendor_bank_account_service import VendorBankAccountService
from app.services.vendor_razorpay_contact_service import VendorRazorpayContactService
from app.services.vendor_razorpay_fund_account_service import VendorRazorpayFundAccountService


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
        return await self.vendor_bank_account_service.list_by_vendor_id(
            vendor.id,
            with_relations={"razorpay_fund_account": True},
        )


class CreateVendorRazorpayContactUseCase(BaseUseCase):
    def __init__(
        self,
        vendor_razorpay_contact_service: VendorRazorpayContactService,
        user_service: UserService,
        razorpay_service: RazorpayService,
    ):
        self.vendor_razorpay_contact_service = vendor_razorpay_contact_service
        self.user_service = user_service
        self.razorpay_service = razorpay_service

    async def execute(self, vendor_id: str) -> dict:
        vendor = await self.user_service.get_user_by_public_id(vendor_id)
        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found.",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        existing_contact = await self.vendor_razorpay_contact_service.get_by_vendor_id(vendor.id)
        if existing_contact:
            return {
                "id": existing_contact.razorpay_contact_id,
                "vendor_id": str(vendor.public_id),
                "name": existing_contact.name,
                "email": existing_contact.email,
                "contact": existing_contact.phone,
                "type": existing_contact.type,
                "reference_id": existing_contact.reference_id,
                "already_exists": True,
            }

        contact_res = await self.razorpay_service.create_contact(
            name=vendor.full_name or "Vendor",
            email=vendor.email,
            contact=vendor.phone,
            type="vendor",
            reference_id=str(vendor.public_id),
            notes={
                "vendor_id": str(vendor.public_id),
                "user_id": str(vendor.id),
            },
        )

        contact_entity = VendorRazorpayContact(
            vendor_id=vendor.id,
            razorpay_contact_id=contact_res.get("id"),
            name=contact_res.get("name") or vendor.full_name or "Vendor",
            email=contact_res.get("email") or vendor.email,
            phone=contact_res.get("contact") or vendor.phone,
            type=contact_res.get("type", "vendor"),
            reference_id=contact_res.get("reference_id") or str(vendor.public_id),
            active=contact_res.get("active", True),
            raw_response=json.dumps(contact_res) if isinstance(contact_res, dict) else str(contact_res),
        )
        await self.vendor_razorpay_contact_service.create(contact_entity)
        return contact_res


class CreateVendorBankAccountUseCase(BaseUseCase):
    def __init__(
        self,
        vendor_bank_account_service: VendorBankAccountService,
        vendor_razorpay_contact_service: VendorRazorpayContactService,
        vendor_razorpay_fund_account_service: VendorRazorpayFundAccountService,
        user_service: UserService,
        razorpay_service: RazorpayService,
    ):
        self.vendor_bank_account_service = vendor_bank_account_service
        self.vendor_razorpay_contact_service = vendor_razorpay_contact_service
        self.vendor_razorpay_fund_account_service = vendor_razorpay_fund_account_service
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

        created_account = await self.vendor_bank_account_service.create(bank_account)

        # Attempt to create Razorpay Contact & Fund Account if Razorpay is configured
        if self.razorpay_service.is_configured():
            try:
                # 1. Reuse existing Razorpay Contact or create new one
                contact = await self.vendor_razorpay_contact_service.get_by_vendor_id(vendor.id)
                if not contact:
                    contact_res = await self.razorpay_service.create_contact(
                        name=vendor.full_name or data.account_holder_name,
                        email=vendor.email,
                        contact=vendor.phone,
                        type="vendor",
                        reference_id=str(vendor.public_id),
                        notes={
                            "vendor_id": str(vendor.public_id),
                            "user_id": str(vendor.id),
                        },
                    )
                    contact = VendorRazorpayContact(
                        vendor_id=vendor.id,
                        razorpay_contact_id=contact_res.get("id"),
                        name=contact_res.get("name") or vendor.full_name or data.account_holder_name,
                        email=contact_res.get("email") or vendor.email,
                        phone=contact_res.get("contact") or vendor.phone,
                        type=contact_res.get("type", "vendor"),
                        reference_id=contact_res.get("reference_id") or str(vendor.public_id),
                        active=contact_res.get("active", True),
                        raw_response=json.dumps(contact_res) if isinstance(contact_res, dict) else str(contact_res),
                    )
                    contact = await self.vendor_razorpay_contact_service.create(contact)

                # 2. Create Fund Account on Razorpay (Bank or UPI VPA)
                if account_type == BankAccountType.VPA and data.upi_id:
                    fa_res = await self.razorpay_service.create_fund_account_vpa(
                        contact_id=contact.razorpay_contact_id,
                        vpa_address=data.upi_id,
                    )
                else:
                    fa_res = await self.razorpay_service.create_fund_account_bank(
                        contact_id=contact.razorpay_contact_id,
                        account_holder_name=data.account_holder_name,
                        account_number=data.account_number,
                        ifsc=data.ifsc_code,
                    )

                fund_account = VendorRazorpayFundAccount(
                    contact_id=contact.id,
                    bank_account_id=created_account.id,
                    razorpay_fund_account_id=fa_res.get("id"),
                    account_type=account_type.value,
                    active=fa_res.get("active", True),
                    raw_response=json.dumps(fa_res) if isinstance(fa_res, dict) else str(fa_res),
                )
                await self.vendor_razorpay_fund_account_service.create(fund_account)
                created_account.is_verified = True
                created_account = await self.vendor_bank_account_service.update(created_account)
            except AppException:
                # If Razorpay call fails (e.g. invalid test keys/sandbox), we still keep bank account locally for manual processing
                pass

        # Reload with relations so razorpay_fund_account is loaded
        reloaded = await self.vendor_bank_account_service.get_by_id(
            created_account.id,
            with_relations={"razorpay_fund_account": True},
        )
        return reloaded or created_account


class SetPrimaryVendorBankAccountUseCase(BaseUseCase):
    def __init__(
        self,
        vendor_bank_account_service: VendorBankAccountService,
        user_service: UserService,
    ):
        self.vendor_bank_account_service = vendor_bank_account_service
        self.user_service = user_service

    async def execute(self, vendor_id: str, bank_account_id: str) -> VendorBankAccount:
        vendor = await self.user_service.get_user_by_public_id(vendor_id)
        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found.",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        bank_account = await self.vendor_bank_account_service.get_by_public_id(bank_account_id)
        if not bank_account or bank_account.vendor_id != vendor.id:
            raise AppException(
                status_code=404,
                message="Vendor bank account not found.",
                error_code="BANK_ACCOUNT_NOT_FOUND",
                field="bank_account_id",
            )

        updated = await self.vendor_bank_account_service.set_primary(bank_account.id, vendor.id)
        reloaded = await self.vendor_bank_account_service.get_by_id(
            bank_account.id,
            with_relations={"razorpay_fund_account": True},
        )
        return reloaded or updated or bank_account


class DeleteVendorBankAccountUseCase(BaseUseCase):
    def __init__(
        self,
        vendor_bank_account_service: VendorBankAccountService,
        user_service: UserService,
    ):
        self.vendor_bank_account_service = vendor_bank_account_service
        self.user_service = user_service

    async def execute(self, vendor_id: str, bank_account_id: str) -> bool:
        vendor = await self.user_service.get_user_by_public_id(vendor_id)
        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found.",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        bank_account = await self.vendor_bank_account_service.get_by_public_id(bank_account_id)
        if not bank_account or bank_account.vendor_id != vendor.id:
            raise AppException(
                status_code=404,
                message="Vendor bank account not found.",
                error_code="BANK_ACCOUNT_NOT_FOUND",
                field="bank_account_id",
            )

        await self.vendor_bank_account_service.delete(bank_account)
        return True
