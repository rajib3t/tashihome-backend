from __future__ import annotations

from app.application.dto.agreements.agreement_template_dto import AgreementTemplateQueryDTO
from app.repositories.base_repository import Page
from app.schemas.agreement_template_schema import AgreementTemplateSchema
from app.services.agreement_template_service import AgreementTemplateService


class ListAgreementTemplatesUseCase:
    def __init__(self, template_service: AgreementTemplateService):
        self.template_service = template_service

    async def execute(self, query: AgreementTemplateQueryDTO) -> Page[AgreementTemplateSchema]:
        return await self.template_service.list_templates(query)

