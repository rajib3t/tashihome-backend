from typing import Optional, TypedDict

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.vendor_bank_account_model import VendorBankAccount
from app.models.vendor_razorpay_fund_account_model import VendorRazorpayFundAccount
from app.repositories.base_repository import BaseRepository, Page


class VendorBankAccountWithRelations(TypedDict, total=False):
    vendor: bool
    razorpay_fund_account: bool


class VendorBankAccountRepository(BaseRepository[VendorBankAccount]):
    _relation_map = {
        "vendor": VendorBankAccount.vendor,
        "razorpay_fund_account": selectinload(VendorBankAccount.razorpay_fund_account).selectinload(
            VendorRazorpayFundAccount.contact
        ),
    }

    async def create(
        self,
        bank_account: VendorBankAccount,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        commit: bool = True,
    ) -> VendorBankAccount:
        # If this is marked as primary, reset existing primary accounts for this vendor
        if bank_account.is_primary:
            await self.db.execute(
                update(VendorBankAccount)
                .where(VendorBankAccount.vendor_id == bank_account.vendor_id)
                .values(is_primary=False)
            )

        self.db.add(bank_account)
        if commit:
            await self.db.commit()
            await self.db.refresh(bank_account)
        if with_relations:
            query = self._apply_relations(
                select(VendorBankAccount).where(VendorBankAccount.id == bank_account.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return bank_account

    async def get_by_id(
        self,
        bank_account_id: int,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        flush: bool = False,
    ) -> Optional[VendorBankAccount]:
        query = select(VendorBankAccount).where(VendorBankAccount.id == bank_account_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        flush: bool = False,
    ) -> Optional[VendorBankAccount]:
        query = select(VendorBankAccount).where(VendorBankAccount.public_id == public_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def get_primary_by_vendor_id(
        self,
        vendor_id: int,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        flush: bool = False,
    ) -> Optional[VendorBankAccount]:
        query = (
            select(VendorBankAccount)
            .where(
                VendorBankAccount.vendor_id == vendor_id,
                VendorBankAccount.is_primary == True,
            )
            .order_by(VendorBankAccount.created_at.desc())
        )
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def list_by_vendor_id(
        self,
        vendor_id: int,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        flush: bool = False,
    ) -> list[VendorBankAccount]:
        query = (
            select(VendorBankAccount)
            .where(VendorBankAccount.vendor_id == vendor_id)
            .order_by(VendorBankAccount.is_primary.desc(), VendorBankAccount.created_at.desc())
        )
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_all(query, flush=flush)

    async def update(
        self,
        bank_account: VendorBankAccount,
        with_relations: Optional[VendorBankAccountWithRelations] = None,
        commit: bool = True,
    ) -> VendorBankAccount:
        if bank_account.is_primary:
            await self.db.execute(
                update(VendorBankAccount)
                .where(
                    VendorBankAccount.vendor_id == bank_account.vendor_id,
                    VendorBankAccount.id != bank_account.id,
                )
                .values(is_primary=False)
            )

        self.db.add(bank_account)
        if commit:
            await self.db.commit()
            await self.db.refresh(bank_account)
        if with_relations:
            query = self._apply_relations(
                select(VendorBankAccount).where(VendorBankAccount.id == bank_account.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return bank_account

    async def set_primary(
        self,
        bank_account_id: int,
        vendor_id: int,
    ) -> Optional[VendorBankAccount]:
        """Sets the specified bank account as primary and resets all other accounts for this vendor."""
        await self.db.execute(
            update(VendorBankAccount)
            .where(VendorBankAccount.vendor_id == vendor_id)
            .values(is_primary=False)
        )
        await self.db.execute(
            update(VendorBankAccount)
            .where(
                VendorBankAccount.id == bank_account_id,
                VendorBankAccount.vendor_id == vendor_id,
            )
            .values(is_primary=True)
        )
        await self.db.commit()
        return await self.get_by_id(bank_account_id)

    async def delete(
        self,
        bank_account: VendorBankAccount,
        commit: bool = True,
    ) -> None:
        await self.db.delete(bank_account)
        if commit:
            await self.db.commit()

