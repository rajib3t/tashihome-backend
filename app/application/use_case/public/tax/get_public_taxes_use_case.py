from typing import List, Optional
from app.application.use_case.base_use_case import BaseUseCase
from app.models.tax_model import Tax
from app.services.tax_service import TaxService


class GetPublicTaxesUseCase(BaseUseCase):
    def __init__(self, tax_service: TaxService):
        self.tax_service = tax_service

    async def execute(self) -> List[Tax]:
        return await self.tax_service.get_active_taxes()


class GetDefaultTaxUseCase(BaseUseCase):
    def __init__(self, tax_service: TaxService):
        self.tax_service = tax_service

    async def execute(self) -> Optional[Tax]:
        return await self.tax_service.get_default_tax()

