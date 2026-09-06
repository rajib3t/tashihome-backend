from typing import Optional, List
from uuid import UUID
from app.models.tax_model import Tax, TaxStatus, TaxType
from app.repositories.base_repository import Page
from app.repositories.tax_repository import TaxRepository


class TaxNotFoundError(Exception):
    def __init__(self, identifier: str):
        super().__init__(f"Tax '{identifier}' not found.")


class TaxService:
    def __init__(self, repository: TaxRepository):
        self.repository = repository

    async def get_by_id(self, tax_id: int) -> Optional[Tax]:
        return await self.repository.get_by_id(tax_id)

    async def get_by_public_id(self, public_id: str) -> Optional[Tax]:
        return await self.repository.get_by_public_id(public_id)

    async def get_by_code(self, code: str) -> Optional[Tax]:
        return await self.repository.get_by_code(code)

    async def get_by_identifier(self, identifier: str) -> Optional[Tax]:
        """Resolve a tax by UUID string, numeric ID, or code."""
        try:
            uuid_obj = UUID(identifier)
            tax = await self.get_by_public_id(str(uuid_obj))
            if tax:
                return tax
        except (ValueError, AttributeError):
            pass

        if str(identifier).isdigit():
            tax = await self.get_by_id(int(identifier))
            if tax:
                return tax

        return await self.get_by_code(identifier)

    async def get_default_tax(self) -> Optional[Tax]:
        return await self.repository.get_default()

    async def get_active_taxes(self) -> List[Tax]:
        return await self.repository.get_active_taxes()

    async def list_taxes(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
    ) -> Page[Tax]:
        return await self.repository.list(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
        )

    async def create_tax(self, tax: Tax, commit: bool = True) -> Tax:
        if tax.is_default:
            await self.repository.unset_other_defaults(commit=False)
        return await self.repository.create(tax, commit=commit)

    async def update_tax(self, tax: Tax, commit: bool = True) -> Tax:
        if tax.is_default:
            await self.repository.unset_other_defaults(except_tax_id=tax.id, commit=False)
        return await self.repository.update(tax, commit=commit)

    async def delete_tax(self, tax: Tax, commit: bool = True) -> None:
        await self.repository.delete(tax, commit=commit)

