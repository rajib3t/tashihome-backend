from typing import List, Optional

from app.models.vendor_razorpay_fund_account_model import VendorRazorpayFundAccount
from app.repositories.vendor_razorpay_fund_account_repository import VendorRazorpayFundAccountRepository


class VendorRazorpayFundAccountService:
    def __init__(self, repository: VendorRazorpayFundAccountRepository):
        self.repository = repository

    async def create(
        self,
        fund_account: VendorRazorpayFundAccount,
        commit: bool = True,
    ) -> VendorRazorpayFundAccount:
        return await self.repository.create(fund_account, commit=commit)

    async def get_by_bank_account_id(
        self,
        bank_account_id: int,
    ) -> Optional[VendorRazorpayFundAccount]:
        return await self.repository.get_by_bank_account_id(bank_account_id)

    async def list_by_contact_id(
        self,
        contact_id: int,
    ) -> List[VendorRazorpayFundAccount]:
        return await self.repository.list_by_contact_id(contact_id)

    async def list_by_vendor_id(
        self,
        vendor_id: int,
    ) -> List[VendorRazorpayFundAccount]:
        return await self.repository.list_by_vendor_id(vendor_id)

    async def get_by_razorpay_id(
        self,
        razorpay_fund_account_id: str,
    ) -> Optional[VendorRazorpayFundAccount]:
        return await self.repository.get_by_razorpay_id(razorpay_fund_account_id)
