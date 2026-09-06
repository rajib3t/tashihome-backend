from typing import Optional

from sqlalchemy import select

from app.models.vendor_razorpay_contact_model import VendorRazorpayContact
from app.repositories.base_repository import BaseRepository


class VendorRazorpayContactRepository(BaseRepository[VendorRazorpayContact]):

    async def create(
        self,
        contact: VendorRazorpayContact,
        commit: bool = True,
    ) -> VendorRazorpayContact:
        self.db.add(contact)
        if commit:
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def get_by_vendor_id(
        self,
        vendor_id: int,
    ) -> Optional[VendorRazorpayContact]:
        query = select(VendorRazorpayContact).where(
            VendorRazorpayContact.vendor_id == vendor_id
        )
        return await self._fetch_one(query)

    async def get_by_razorpay_id(
        self,
        razorpay_contact_id: str,
    ) -> Optional[VendorRazorpayContact]:
        query = select(VendorRazorpayContact).where(
            VendorRazorpayContact.razorpay_contact_id == razorpay_contact_id
        )
        return await self._fetch_one(query)

    async def get_by_public_id(
        self,
        public_id: str,
    ) -> Optional[VendorRazorpayContact]:
        query = select(VendorRazorpayContact).where(
            VendorRazorpayContact.public_id == public_id
        )
        return await self._fetch_one(query)
