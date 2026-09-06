from typing import Optional
from sqlalchemy import select, update
from app.models.tax_model import Tax, TaxStatus
from app.repositories.base_repository import BaseRepository, Page


class TaxRepository(BaseRepository[Tax]):
    _filter_map = {
        "name": Tax.name,
        "code": Tax.code,
        "status": Tax.status,
        "tax_type": Tax.tax_type,
        "is_default": Tax.is_default,
        "is_inclusive": Tax.is_inclusive,
    }

    async def get_by_id(self, tax_id: int, flush: bool = False) -> Optional[Tax]:
        query = select(Tax).where(Tax.id == tax_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Optional[Tax]:
        query = select(Tax).where(Tax.public_id == public_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_code(self, code: str, flush: bool = False) -> Optional[Tax]:
        query = select(Tax).where(Tax.code == code.strip().upper())
        return await self._fetch_one(query, flush=flush)

    async def get_by_name(self, name: str, flush: bool = False) -> Optional[Tax]:
        query = select(Tax).where(Tax.name.ilike(name.strip()))
        return await self._fetch_one(query, flush=flush)

    async def get_default(self, flush: bool = False) -> Optional[Tax]:
        query = select(Tax).where(Tax.is_default.is_(True), Tax.status == TaxStatus.ACTIVE).limit(1)
        return await self._fetch_one(query, flush=flush)

    async def unset_other_defaults(self, except_tax_id: Optional[int] = None, commit: bool = True) -> None:
        stmt = update(Tax).where(Tax.is_default.is_(True))
        if except_tax_id:
            stmt = stmt.where(Tax.id != except_tax_id)
        stmt = stmt.values(is_default=False)
        await self.db.execute(stmt)
        if commit:
            await self.db.commit()

    async def get_active_taxes(self, flush: bool = False) -> list[Tax]:
        query = select(Tax).where(Tax.status == TaxStatus.ACTIVE).order_by(Tax.is_default.desc(), Tax.created_at.desc())
        return await self._fetch_all(query, flush=flush)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        flush: bool = False,
    ) -> Page[Tax]:
        query = select(Tax).order_by(Tax.is_default.desc(), Tax.created_at.desc())
        query = self._apply_search(query, search, search_fields=[Tax.name, Tax.code, Tax.gst_number, Tax.legal_name])
        query = self._apply_dynamic_filters(query, filters, self._filter_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def create(self, tax: Tax, commit: bool = True) -> Tax:
        self.db.add(tax)
        if commit:
            await self.db.commit()
            await self.db.refresh(tax)
        return tax

    async def update(self, tax: Tax, commit: bool = True) -> Tax:
        self.db.add(tax)
        if commit:
            await self.db.commit()
            await self.db.refresh(tax)
        return tax

    async def delete(self, tax: Tax, commit: bool = True) -> None:
        await self.db.delete(tax)
        if commit:
            await self.db.commit()

