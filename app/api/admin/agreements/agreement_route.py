from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.api.base_controller import BaseController
from app.application.dto.agreements.agreement_dto import (
    AdminCountersignAgreementDTO,
    AgreementQueryDTO,
    SendVendorAgreementDTO,
)
from app.application.use_case.admin.vendors.cancel_agreement_use_case import CancelAgreementUseCase
from app.application.use_case.admin.vendors.list_agreements_use_case import ListAgreementsUseCase
from app.application.use_case.admin.vendors.resend_agreement_use_case import ResendAgreementUseCase
from app.application.use_case.admin.vendors.send_agreement_use_case import SendVendorAgreementUseCase
from app.core.exceptions import AppException
from app.deps.agreement import (
    get_cancel_agreement_use_case,
    get_list_agreements_use_case,
    get_resend_agreement_use_case,
    get_send_vendor_agreement_use_case,
)
from app.deps.auth import get_current_user
from app.deps.service import get_vendor_agreement_service
from app.schemas.response import BaseResponse
from app.schemas.vendor_agreement_schema import (
    VendorAgreementListResponseSchema,
    VendorAgreementResponseSchema,
)
from app.services.vendor_agreement_service import VendorAgreementService
from app.utils.exception_decorate import handle_api_exceptions


class AgreementController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/agreements",
            tags=["Admin - Host Agreements & E-Sign"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._list_agreements, {"response_model": VendorAgreementListResponseSchema}),
            ("post", "/send/{vendor_id}", self._send_agreement, {"response_model": VendorAgreementResponseSchema, "status_code": 201}),
            ("post", "/vendors/{vendor_id}/send", self._send_agreement, {"response_model": VendorAgreementResponseSchema, "status_code": 201}),
            ("get", "/{agreement_id}", self._get_agreement, {"response_model": VendorAgreementResponseSchema}),
            ("post", "/{agreement_id}/resend", self._resend_agreement, {"response_model": VendorAgreementResponseSchema}),
            ("post", "/{agreement_id}/countersign", self._countersign_agreement, {"response_model": VendorAgreementResponseSchema}),
            ("delete", "/{agreement_id}", self._cancel_agreement, {"response_model": VendorAgreementResponseSchema}),
            ("get", "/{agreement_id}/download-pdf", self._download_pdf, {"response_model": None}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _list_agreements(
        self,
        params: AgreementQueryDTO = Depends(),
        use_case: ListAgreementsUseCase = Depends(get_list_agreements_use_case),
    ):
        page = await use_case.execute(params)
        return self.build_response(
            message="Agreements retrieved successfully.",
            data=page.items,
            meta=self.pagination_meta(page),
        )

    @handle_api_exceptions
    async def _send_agreement(
        self,
        vendor_id: str,
        data: SendVendorAgreementDTO,
        use_case: SendVendorAgreementUseCase = Depends(get_send_vendor_agreement_use_case),
    ):
        agreement = await use_case.execute(vendor_id, data)
        return self.build_response(
            message="Host agreement dispatched successfully.",
            data=agreement,
        )

    @handle_api_exceptions
    async def _get_agreement(
        self,
        agreement_id: str,
        agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
    ):
        agreement = await agreement_service.get_by_public_id(agreement_id)
        if not agreement:
            raise AppException(status_code=404, message="Agreement not found.", error_code="NOT_FOUND")
        return self.build_response(
            message="Agreement retrieved successfully.",
            data=agreement,
        )

    @handle_api_exceptions
    async def _resend_agreement(
        self,
        agreement_id: str,
        use_case: ResendAgreementUseCase = Depends(get_resend_agreement_use_case),
    ):
        agreement = await use_case.execute(agreement_id)
        return self.build_response(
            message="Agreement re-sent successfully.",
            data=agreement,
        )

    @handle_api_exceptions
    async def _countersign_agreement(
        self,
        agreement_id: str,
        data: Optional[AdminCountersignAgreementDTO] = None,
        agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
        current_user = Depends(get_current_user),
    ):
        agreement = await agreement_service.countersign_agreement(
            agreement_id=agreement_id,
            admin_user=current_user,
            data=data,
        )
        return self.build_response(
            message="Agreement countersigned successfully.",
            data=agreement,
        )

    @handle_api_exceptions
    async def _cancel_agreement(
        self,
        agreement_id: str,
        use_case: CancelAgreementUseCase = Depends(get_cancel_agreement_use_case),
    ):
        agreement = await use_case.execute(agreement_id)
        return self.build_response(
            message="Agreement cancelled successfully.",
            data=agreement,
        )

    @handle_api_exceptions
    async def _download_pdf(
        self,
        agreement_id: str,
        agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
    ):
        agreement = await agreement_service.get_by_public_id(agreement_id)
        if not agreement:
            raise AppException(status_code=404, message="Agreement not found.")
        url = await agreement_service.get_download_url(agreement)
        if not url:
            raise AppException(status_code=404, message="Agreement PDF not available or not yet executed.")
        return RedirectResponse(url=url)


controller = AgreementController()
router = controller.router

