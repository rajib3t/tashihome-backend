from typing import Optional

from sqlalchemy import select

from app.models.address_model import Address
from app.repositories.base_repository import BaseRepository


class AddressRepository(BaseRepository[Address]):
    async def get_company_address_by_owner_id(
        self,
        owner_id: int,
        flush: bool = False,
    ) -> Optional[Address]:
        query = select(Address).where(
            Address.owner_type == "company",
            Address.owner_id == owner_id,
        )
        return await self._fetch_one(query, flush=flush)


    async def create(
        self,
        address: Address,
        commit: bool = True,
    ) -> Address:
        self.db.add(address)

        if not commit:
            return address

        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def update(
        self,
        address: Address,
        commit: bool = True,
    ) -> Address:
        if not commit:
            return address

        await self.db.commit()
        await self.db.refresh(address)
        return address