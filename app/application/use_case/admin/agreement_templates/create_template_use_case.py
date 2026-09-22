from __future__ import annotations

from typing import Optional
from fastapi import UploadFile

from app.application.dto.agreements.agreement_template_dto import CreateAgreementTemplateDTO
from app.deps.auth import CurrentUser
from app.schemas.agreement_template_schema import AgreementTemplateSchema
from app.services.agreement_template_service import AgreementTemplateService


class CreateAgreementTemplateUseCase:
    def __init__(self, template_service: AgreementTemplateService, current_user: CurrentUser):
        self.template_service = template_service
        self.current_user = current_user

    async def execute(
        self,
        dto: CreateAgreementTemplateDTO,
        pdf_file: Optional[UploadFile] = None,
    ) -> AgreementTemplateSchema:
        return await self.template_service.create_template(
            dto=dto,
            pdf_file=pdf_file,
            created_by_id=self.current_user.id,
        )

