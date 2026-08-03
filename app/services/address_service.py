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
