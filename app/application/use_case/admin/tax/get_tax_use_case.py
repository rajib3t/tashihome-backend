from typing import Optional
from app.application.dto.tax import TaxQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.tax_model import Tax
from app.repositories.base_repository import Page
from app.services.tax_service import TaxService


class GetTaxUseCase(BaseUseCase):
    def __init__(self, tax_service: TaxService):
        self.tax_service = tax_service

    async def execute(self, identifier: str) -> Tax:
        tax = await self.tax_service.get_by_identifier(identifier)
        if not tax:
            raise AppException(
                status_code=404,
                message=f"Tax with identifier '{identifier}' not found.",
                error_code="TAX_NOT_FOUND",
            )
        return tax


class ListTaxesUseCase(BaseUseCase):
    def __init__(self, tax_service: TaxService):
        self.tax_service = tax_service

    async def execute(self, params: TaxQueryDTO) -> Page[Tax]:
        filters: list[dict[str, str]] = []
        if params.status:
            filters.append({"name": "status", "value": params.status})
        if params.is_default is not None:
            filters.append({"name": "is_default", "value": str(params.is_default).lower()})

        return await self.tax_service.list_taxes(
            page=params.page,
            page_size=params.size,
            search=params.search,
            filters=filters,
        )

