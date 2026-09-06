from typing import Optional

from app.models.vendor_razorpay_contact_model import VendorRazorpayContact
from app.repositories.vendor_razorpay_contact_repository import VendorRazorpayContactRepository


class VendorRazorpayContactService:
    def __init__(self, repository: VendorRazorpayContactRepository):
        self.repository = repository

    async def create(
        self,
        contact: VendorRazorpayContact,
        commit: bool = True,
    ) -> VendorRazorpayContact:
        return await self.repository.create(contact, commit=commit)

    async def get_by_vendor_id(
        self,
        vendor_id: int,
    ) -> Optional[VendorRazorpayContact]:
        return await self.repository.get_by_vendor_id(vendor_id)

    async def get_by_razorpay_id(
        self,
        razorpay_contact_id: str,
    ) -> Optional[VendorRazorpayContact]:
        return await self.repository.get_by_razorpay_id(razorpay_contact_id)

    async def get_by_public_id(
        self,
        public_id: str,
    ) -> Optional[VendorRazorpayContact]:
        return await self.repository.get_by_public_id(public_id)
