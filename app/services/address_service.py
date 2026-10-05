from __future__ import annotations
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
        return await self.address_repository.get_address_by_owner_id(
            owner_id=owner_id,
            owner_type="company",
            flush=flush,
        )


    async def get_user_address_by_owner_id(
        self,
        owner_id: int,
        flush: bool = False,
    ) -> Optional[Address]:
        return await self.address_repository.get_address_by_owner_id(
            owner_id=owner_id,
            owner_type='user',
            flush=flush,
        )

    async def get_property_address_by_owner_id(
        self,
        owner_id: int,
        flush: bool = False,
    ) -> Optional[Address]:
        return await self.address_repository.get_address_by_owner_id(
            owner_id=owner_id,
            owner_type="property",
            flush=flush,
        )
  
    async def create_address(
        self,
        address: Address,
        commit: bool = True,
    ) -> Address:
        return await self.address_repository.create(address, commit=commit)

    async def create(
        self,
        address: Address,
        commit: bool = True,
    ) -> Address:
        return await self.create_address(address=address, commit=commit)

    async def persist_company_address(
        self,
        address: Address,
        commit: bool = True,
    ) -> Address:
        return await self.address_repository.update(address, commit=commit)

    async def update(
        self,
        address: Address,
        commit: bool = True,
    ) -> Address:
        return await self.persist_company_address(address=address, commit=commit)

    async def sync_property_address(
        self,
        property_id: int,
        address_line1: str,
        address_line2: Optional[str] = None,
        postal_code: str = "000000",
        country: str = "India",
        commit: bool = True,
    ) -> Address:
        existing = await self.get_property_address_by_owner_id(property_id, flush=False)
        if existing:
            existing.address_line1 = address_line1
            existing.address_line2 = address_line2
            existing.postal_code = postal_code
            existing.country = country
            return await self.address_repository.update(existing, commit=commit)
        else:
            new_addr = Address(
                owner_type="property",
                owner_id=property_id,
                address_line1=address_line1,
                address_line2=address_line2,
                postal_code=postal_code,
                country=country,
            )
            return await self.address_repository.create(new_addr, commit=commit)

