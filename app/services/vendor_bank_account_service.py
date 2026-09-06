from typing import Optional

from app.models.vendor_bank_account_model import VendorBankAccount
from app.repositories.vendor_bank_account_repository import (
    VendorBankAccountRepository,
    VendorBankAccountWithRelations,
)


class VendorBankAccountService:
    def __init__(self, repository: VendorBankAccountRepository):
        self.repository = repository

    async def create(
        self,
        bank_account: VendorBankAccount,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        commit: bool = True,
    ) -> VendorBankAccount:
        return await self.repository.create(bank_account, with_relations=with_relations, commit=commit)

    async def get_by_id(
        self,
        bank_account_id: int,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        flush: bool = False,
    ) -> Optional[VendorBankAccount]:
        return await self.repository.get_by_id(bank_account_id, with_relations=with_relations, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        flush: bool = False,
    ) -> Optional[VendorBankAccount]:
        return await self.repository.get_by_public_id(public_id, with_relations=with_relations, flush=flush)

    async def get_primary_by_vendor_id(
        self,
        vendor_id: int,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        flush: bool = False,
    ) -> Optional[VendorBankAccount]:
        return await self.repository.get_primary_by_vendor_id(vendor_id, with_relations=with_relations, flush=flush)

    async def list_by_vendor_id(
        self,
        vendor_id: int,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        flush: bool = False,
    ) -> list[VendorBankAccount]:
        return await self.repository.list_by_vendor_id(vendor_id, with_relations=with_relations, flush=flush)

    async def update(
        self,
        bank_account: VendorBankAccount,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        commit: bool = True,
    ) -> VendorBankAccount:
        return await self.repository.update(bank_account, with_relations=with_relations, commit=commit)

    async def set_primary(
        self,
        bank_account_id: int,
        vendor_id: int,
    ) -> Optional[VendorBankAccount]:
        return await self.repository.set_primary(bank_account_id, vendor_id)

    async def delete(
        self,
        bank_account: VendorBankAccount,
        commit: bool = True,
    ) -> None:
        await self.repository.delete(bank_account, commit=commit)

