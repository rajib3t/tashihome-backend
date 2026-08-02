from typing import Optional

from app.models.address_model import Address
from app.repositories.address_repository import AddressRepository


class AddressService:
    def __init__(self, address_repository: AddressRepository):
        self.address_repository = address_repository

    async def get_company_address_by_owner_id(
        self,
        owner_id: int,
        flush: bool = False,
    ) -> Optional[Address]:
        return await self.address_repository.get_company_address_by_owner_id(
            owner_id=owner_id,
            flush=flush,
        )

    async def update_company_address(
        self,
        address: Address,
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Address:
        if address_line1 is not None:
            address.address_line1 = address_line1
        if address_line2 is not None:
            address.address_line2 = address_line2
        if postal_code is not None:
            address.postal_code = postal_code
        if country is not None:
            address.country = country
        return address

    async def create_address(
        self,
        address: Address,
        commit: bool = True,
    ) -> Address:
        return await self.address_repository.create(address, commit=commit)

    async def persist_company_address(
        self,
        address: Address,
        commit: bool = True,
    ) -> Address:
        return await self.address_repository.update(address, commit=commit)
