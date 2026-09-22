from __future__ import annotations

from typing import Optional
from fastapi import UploadFile

from app.application.dto.agreements.agreement_template_dto import UpdateAgreementTemplateDTO
from app.schemas.agreement_template_schema import AgreementTemplateSchema
from app.services.agreement_template_service import AgreementTemplateService


class UpdateAgreementTemplateUseCase:
    def __init__(self, template_service: AgreementTemplateService):
        self.template_service = template_service

    async def execute(
        self,
        template_id: str,
        dto: UpdateAgreementTemplateDTO,
        pdf_file: Optional[UploadFile] = None,
    ) -> AgreementTemplateSchema:
        return await self.template_service.update_template(
            template_id=template_id,
            dto=dto,
            pdf_file=pdf_file,
        )

