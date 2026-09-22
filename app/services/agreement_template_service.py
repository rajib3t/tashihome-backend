from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import UploadFile

from app.application.dto.agreements.agreement_template_dto import (
    AgreementTemplateQueryDTO,
    CreateAgreementTemplateDTO,
    UpdateAgreementTemplateDTO,
)
from app.core.exceptions import AppException
from app.models.agreement_template_model import (
    AgreementTemplate,
    AgreementTemplateStatus,
    AgreementTemplateType,
)
from app.repositories.agreement_template_repository import AgreementTemplateRepository
from app.repositories.base_repository import Page
from app.schemas.agreement_template_schema import AgreementTemplateSchema
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

PDF_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


class AgreementTemplateService:
    def __init__(
        self,
        repository: AgreementTemplateRepository,
        storage_service: StorageService,
    ):
        self.repository = repository
        self.storage_service = storage_service

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _resolve_schema(self, template: AgreementTemplate) -> AgreementTemplateSchema:
        pdf_url: Optional[str] = None
        if template.template_type == AgreementTemplateType.PDF_UPLOAD and template.pdf_file_key:
            try:
                pdf_url = await self.storage_service.get_display_url(template.pdf_file_key)
            except Exception as exc:
                logger.warning("Could not resolve PDF URL for template %s: %s", template.public_id, exc)
        return AgreementTemplateSchema.from_orm_with_url(template, pdf_url=pdf_url)

    async def _upload_pdf(self, pdf_file: UploadFile, old_key: Optional[str] = None) -> str:
        if pdf_file.content_type not in ("application/pdf", "application/octet-stream") and not (pdf_file.filename or "").lower().endswith(".pdf"):
            raise AppException(
                status_code=400,
                message="Only PDF files are allowed for PDF-type templates.",
                error_code="INVALID_FILE_TYPE",
                field="pdf_file",
            )
        data = await pdf_file.read()
        if not data:
            raise AppException(status_code=400, message="Uploaded PDF file is empty.", error_code="EMPTY_FILE", field="pdf_file")
        if len(data) > PDF_MAX_BYTES:
            raise AppException(status_code=413, message="PDF file must be smaller than 10 MB.", error_code="FILE_TOO_LARGE", field="pdf_file")

        from uuid import uuid4
        key = f"agreement_templates/{uuid4().hex}.pdf"
        await self.storage_service.upload_bytes(key, data, content_type="application/pdf")

        # Delete the old PDF if replacing
        if old_key and old_key != key:
            try:
                await self.storage_service.delete_object(old_key)
            except Exception:
                pass

        return key

    # ──────────────────────────────────────────────────────────────────────────
    # Core CRUD
    # ──────────────────────────────────────────────────────────────────────────

    async def create_template(
        self,
        dto: CreateAgreementTemplateDTO,
        pdf_file: Optional[UploadFile] = None,
        created_by_id: Optional[int] = None,
    ) -> AgreementTemplateSchema:
        template_type = AgreementTemplateType(dto.template_type)

        if template_type == AgreementTemplateType.PDF_UPLOAD and pdf_file is None:
            raise AppException(
                status_code=400,
                message="A PDF file is required for PDF-upload type templates.",
                error_code="PDF_REQUIRED",
                field="pdf_file",
            )

        if template_type == AgreementTemplateType.RICH_TEXT and not dto.content_json:
            raise AppException(
                status_code=400,
                message="content_json is required for rich-text type templates.",
                error_code="CONTENT_REQUIRED",
                field="content_json",
            )

        if dto.content_json:
            try:
                json.loads(dto.content_json)
            except Exception:
                raise AppException(status_code=400, message="content_json must be valid JSON.", error_code="INVALID_JSON", field="content_json")

        pdf_file_key: Optional[str] = None
        if template_type == AgreementTemplateType.PDF_UPLOAD:
            pdf_file_key = await self._upload_pdf(pdf_file)

        # If no active templates exist yet, auto-set as default
        existing_default = await self.repository.get_default()
        make_default = existing_default is None and AgreementTemplateStatus(dto.status) == AgreementTemplateStatus.ACTIVE

        template = AgreementTemplate(
            name=dto.name,
            version=dto.version,
            description=dto.description,
            template_type=template_type,
            status=AgreementTemplateStatus(dto.status),
            content_json=dto.content_json,
            pdf_file_key=pdf_file_key,
            is_default=make_default,
            created_by=created_by_id,
        )
        saved = await self.repository.create(template)
        return await self._resolve_schema(saved)

    async def get_template(self, template_id: str) -> AgreementTemplateSchema:
        template = await self._fetch_or_404(template_id)
        return await self._resolve_schema(template)

    async def update_template(
        self,
        template_id: str,
        dto: UpdateAgreementTemplateDTO,
        pdf_file: Optional[UploadFile] = None,
    ) -> AgreementTemplateSchema:
        template = await self._fetch_or_404(template_id)

        if dto.name is not None:
            template.name = dto.name
        if dto.version is not None:
            template.version = dto.version
        if dto.description is not None:
            template.description = dto.description
        if dto.status is not None:
            template.status = AgreementTemplateStatus(dto.status)
        if dto.template_type is not None:
            template.template_type = AgreementTemplateType(dto.template_type)
        if dto.content_json is not None:
            try:
                json.loads(dto.content_json)
            except Exception:
                raise AppException(status_code=400, message="content_json must be valid JSON.", error_code="INVALID_JSON", field="content_json")
            template.content_json = dto.content_json

        if pdf_file is not None:
            template.pdf_file_key = await self._upload_pdf(pdf_file, old_key=template.pdf_file_key)

        updated = await self.repository.update(template)
        return await self._resolve_schema(updated)

    async def set_default(self, template_id: str) -> AgreementTemplateSchema:
        template = await self._fetch_or_404(template_id)
        if template.status != AgreementTemplateStatus.ACTIVE:
            raise AppException(
                status_code=400,
                message="Only active templates can be set as default.",
                error_code="TEMPLATE_NOT_ACTIVE",
            )
        await self.repository.unset_all_defaults()
        template.is_default = True
        updated = await self.repository.update(template)
        return await self._resolve_schema(updated)

    async def archive_template(self, template_id: str) -> AgreementTemplateSchema:
        template = await self._fetch_or_404(template_id)
        if template.is_default:
            # Unset default before archiving
            template.is_default = False
        template.status = AgreementTemplateStatus.ARCHIVED
        updated = await self.repository.update(template)
        return await self._resolve_schema(updated)

    async def list_templates(self, query: AgreementTemplateQueryDTO) -> Page[AgreementTemplateSchema]:
        page = await self.repository.list_templates(
            page=query.page,
            size=query.size,
            status=query.status,
            search=query.search,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        schemas = []
        for t in page.items:
            schemas.append(await self._resolve_schema(t))
        return Page(items=schemas, total=page.total, page=page.page, page_size=page.page_size)

    async def get_preview_data(self, template_id: str) -> Dict[str, Any]:
        """Return clause data for rich_text or a signed PDF URL for pdf_upload."""
        template = await self._fetch_or_404(template_id)
        if template.template_type == AgreementTemplateType.RICH_TEXT:
            clauses = []
            if template.content_json:
                try:
                    clauses = json.loads(template.content_json)
                except Exception:
                    pass
            return {"template_type": "rich_text", "clauses": clauses}
        else:
            pdf_url: Optional[str] = None
            if template.pdf_file_key:
                pdf_url = await self.storage_service.get_display_url(template.pdf_file_key)
            return {"template_type": "pdf_upload", "pdf_url": pdf_url}

    # ──────────────────────────────────────────────────────────────────────────
    # Agreement generation helpers (called by VendorAgreementService)
    # ──────────────────────────────────────────────────────────────────────────

    async def get_clauses_for_agreement(
        self,
        template_id: Optional[str] = None,
    ) -> tuple[List[Dict[str, str]], Optional[str]]:
        """
        Return (clauses_list, pdf_file_key).
        - For rich_text: clauses_list is populated, pdf_file_key is None
        - For pdf_upload: clauses_list is a placeholder, pdf_file_key holds the key
        - Falls back to DEFAULT_HOST_CLAUSES if no template found
        """
        from app.services.agreement_pdf_service import DEFAULT_HOST_CLAUSES

        template: Optional[AgreementTemplate] = None

        if template_id:
            try:
                template = await self.repository.get_by_public_id(UUID(template_id))
            except Exception:
                pass
            if not template:
                logger.warning("Template %s not found, falling back to default.", template_id)

        if template is None:
            template = await self.repository.get_default()

        if template is None:
            return list(DEFAULT_HOST_CLAUSES), None

        if template.template_type == AgreementTemplateType.PDF_UPLOAD:
            placeholder = [{"heading": "Agreement Document", "body": "Please review the attached PDF agreement document and sign below to confirm your acceptance."}]
            return placeholder, template.pdf_file_key

        # Rich text
        if template.content_json:
            try:
                parsed = json.loads(template.content_json)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed, None
            except Exception:
                pass

        return list(DEFAULT_HOST_CLAUSES), None

    # ──────────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_or_404(self, template_id: str) -> AgreementTemplate:
        try:
            uid = UUID(template_id)
            template = await self.repository.get_by_public_id(uid)
        except ValueError:
            template = None

        if not template:
            raise AppException(
                status_code=404,
                message="Agreement template not found.",
                error_code="TEMPLATE_NOT_FOUND",
            )
        return template

