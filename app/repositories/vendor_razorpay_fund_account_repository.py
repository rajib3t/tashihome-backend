from typing import List, Optional

from sqlalchemy import select

from app.models.vendor_razorpay_contact_model import VendorRazorpayContact
from app.models.vendor_razorpay_fund_account_model import VendorRazorpayFundAccount
from app.repositories.base_repository import BaseRepository


class VendorRazorpayFundAccountRepository(BaseRepository[VendorRazorpayFundAccount]):

    async def create(
        self,
        fund_account: VendorRazorpayFundAccount,
        commit: bool = True,
    ) -> VendorRazorpayFundAccount:
        self.db.add(fund_account)
        if commit:
            await self.db.commit()
            await self.db.refresh(fund_account)
        return fund_account

    async def get_by_bank_account_id(
        self,
        bank_account_id: int,
    ) -> Optional[VendorRazorpayFundAccount]:
        query = select(VendorRazorpayFundAccount).where(
            VendorRazorpayFundAccount.bank_account_id == bank_account_id
        )
        return await self._fetch_one(query)

    async def list_by_contact_id(
        self,
        contact_id: int,
    ) -> List[VendorRazorpayFundAccount]:
        query = (
            select(VendorRazorpayFundAccount)
            .where(VendorRazorpayFundAccount.contact_id == contact_id)
            .order_by(VendorRazorpayFundAccount.created_at.desc())
        )
        return await self._fetch_all(query)

    async def list_by_vendor_id(
        self,
        vendor_id: int,
    ) -> List[VendorRazorpayFundAccount]:
        """List all fund accounts for a vendor via their Razorpay contact."""
        query = (
            select(VendorRazorpayFundAccount)
            .join(
                VendorRazorpayContact,
                VendorRazorpayFundAccount.contact_id == VendorRazorpayContact.id,
            )
            .where(VendorRazorpayContact.vendor_id == vendor_id)
            .order_by(VendorRazorpayFundAccount.created_at.desc())
        )
        return await self._fetch_all(query)

    async def get_by_razorpay_id(
        self,
        razorpay_fund_account_id: str,
    ) -> Optional[VendorRazorpayFundAccount]:
        query = select(VendorRazorpayFundAccount).where(
            VendorRazorpayFundAccount.razorpay_fund_account_id == razorpay_fund_account_id
        )
        return await self._fetch_one(query)
