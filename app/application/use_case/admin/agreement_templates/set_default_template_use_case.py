from __future__ import annotations

from app.schemas.agreement_template_schema import AgreementTemplateSchema
from app.services.agreement_template_service import AgreementTemplateService


class SetDefaultTemplateUseCase:
    def __init__(self, template_service: AgreementTemplateService):
        self.template_service = template_service

    async def execute(self, template_id: str) -> AgreementTemplateSchema:
        return await self.template_service.set_default(template_id)

