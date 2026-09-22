from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from fastapi.responses import RedirectResponse

from app.api.base_controller import BaseController
from app.application.dto.agreements.agreement_template_dto import (
    AgreementTemplateQueryDTO,
    CreateAgreementTemplateDTO,
    UpdateAgreementTemplateDTO,
)
from app.application.use_case.admin.agreement_templates.create_template_use_case import CreateAgreementTemplateUseCase
from app.application.use_case.admin.agreement_templates.delete_template_use_case import DeleteAgreementTemplateUseCase
from app.application.use_case.admin.agreement_templates.list_templates_use_case import ListAgreementTemplatesUseCase
from app.application.use_case.admin.agreement_templates.set_default_template_use_case import SetDefaultTemplateUseCase
from app.application.use_case.admin.agreement_templates.update_template_use_case import UpdateAgreementTemplateUseCase
from app.core.exceptions import AppException
from app.deps.agreement import (
    get_create_template_use_case,
    get_delete_template_use_case,
    get_list_templates_use_case,
    get_set_default_template_use_case,
    get_update_template_use_case,
)
from app.deps.service import get_agreement_template_service
from app.schemas.agreement_template_schema import (
    AgreementTemplateListResponseSchema,
    AgreementTemplateResponseSchema,
)
from app.schemas.response import BaseResponse
from app.services.agreement_template_service import AgreementTemplateService
from app.utils.exception_decorate import handle_api_exceptions


class AgreementTemplateController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/agreement-templates",
            tags=["Admin - Agreement Templates"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._list_templates, {"response_model": AgreementTemplateListResponseSchema}),
            ("post", "/", self._create_template, {"response_model": AgreementTemplateResponseSchema, "status_code": 201}),
            ("get", "/{template_id}", self._get_template, {"response_model": AgreementTemplateResponseSchema}),
            ("put", "/{template_id}", self._update_template, {"response_model": AgreementTemplateResponseSchema}),
            ("delete", "/{template_id}", self._archive_template, {"response_model": AgreementTemplateResponseSchema}),
            ("post", "/{template_id}/set-default", self._set_default, {"response_model": AgreementTemplateResponseSchema}),
            ("get", "/{template_id}/preview", self._preview_template, {"response_model": None}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    # ─────────────────────────────────────────────────────────────────────────

    @handle_api_exceptions
    async def _list_templates(
        self,
        query: AgreementTemplateQueryDTO = Depends(),
        use_case: ListAgreementTemplatesUseCase = Depends(get_list_templates_use_case),
    ):
        page = await use_case.execute(query)
        return self.build_response(
            message="Agreement templates retrieved successfully.",
            data=page.items,
            meta=self.pagination_meta(page),
        )

    @handle_api_exceptions
    async def _create_template(
        self,
        request: Request,
        use_case: CreateAgreementTemplateUseCase = Depends(get_create_template_use_case),
    ):
        """
        Create a template. Accepts:
        - application/json: { name, version, description, template_type, content_json, status }
        - multipart/form-data: same fields + optional pdf_file upload
        """
        content_type = request.headers.get("content-type", "")
        pdf_file: Optional[UploadFile] = None
        payload: Dict[str, Any] = {}

        if "multipart/form-data" in content_type:
            form_data = await request.form()
            for key, value in form_data.items():
                if isinstance(value, UploadFile):
                    if bool(getattr(value, "filename", None)):
                        if key == "pdf_file":
                            pdf_file = value
                else:
                    payload[key] = value
        else:
            payload = await request.json()

        dto = CreateAgreementTemplateDTO(**payload)
        result = await use_case.execute(dto=dto, pdf_file=pdf_file)
        return self.build_response("Agreement template created successfully.", data=result)

    @handle_api_exceptions
    async def _get_template(
        self,
        template_id: str,
        template_service: AgreementTemplateService = Depends(get_agreement_template_service),
    ):
        result = await template_service.get_template(template_id)
        return self.build_response("Agreement template retrieved successfully.", data=result)

    @handle_api_exceptions
    async def _update_template(
        self,
        template_id: str,
        request: Request,
        use_case: UpdateAgreementTemplateUseCase = Depends(get_update_template_use_case),
    ):
        content_type = request.headers.get("content-type", "")
        pdf_file: Optional[UploadFile] = None
        payload: Dict[str, Any] = {}

        if "multipart/form-data" in content_type:
            form_data = await request.form()
            for key, value in form_data.items():
                if isinstance(value, UploadFile):
                    if bool(getattr(value, "filename", None)) and key == "pdf_file":
                        pdf_file = value
                else:
                    payload[key] = value
        else:
            payload = await request.json()

        dto = UpdateAgreementTemplateDTO(**payload)
        result = await use_case.execute(template_id=template_id, dto=dto, pdf_file=pdf_file)
        return self.build_response("Agreement template updated successfully.", data=result)

    @handle_api_exceptions
    async def _archive_template(
        self,
        template_id: str,
        use_case: DeleteAgreementTemplateUseCase = Depends(get_delete_template_use_case),
    ):
        result = await use_case.execute(template_id)
        return self.build_response("Agreement template archived successfully.", data=result)

    @handle_api_exceptions
    async def _set_default(
        self,
        template_id: str,
        use_case: SetDefaultTemplateUseCase = Depends(get_set_default_template_use_case),
    ):
        result = await use_case.execute(template_id)
        return self.build_response("Default agreement template updated.", data=result)

    @handle_api_exceptions
    async def _preview_template(
        self,
        template_id: str,
        request: Request,
        template_service: AgreementTemplateService = Depends(get_agreement_template_service),
    ):
        """
        For rich_text: returns { template_type: 'rich_text', clauses: [...] }.
        For pdf_upload: returns { template_type: 'pdf_upload', pdf_url: '...' } (or redirects if ?redirect=true).
        """
        data = await template_service.get_preview_data(template_id)
        if request.query_params.get("redirect", "false").lower() == "true" and data.get("template_type") == "pdf_upload":
            pdf_url = data.get("pdf_url")
            if not pdf_url:
                raise AppException(status_code=404, message="PDF not found for this template.")
            return RedirectResponse(url=pdf_url)
        return self.build_response("Template preview data.", data=data)


controller = AgreementTemplateController()
router = controller.router
