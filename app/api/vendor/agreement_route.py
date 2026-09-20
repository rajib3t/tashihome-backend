from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.api.base_controller import BaseController
from app.application.use_case.vendor.agreements.get_my_agreement_use_case import (
    GetMyVendorAgreementUseCase,
)
from app.core.exceptions import AppException
from app.deps.agreement import get_my_vendor_agreement_use_case
from app.deps.auth import CurrentUser, get_current_user
from app.deps.service import get_vendor_agreement_service
from app.schemas.vendor_agreement_schema import VendorMyAgreementResponseSchema
from app.services.vendor_agreement_service import VendorAgreementService
from app.utils.exception_decorate import handle_api_exceptions


class VendorAgreementController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/agreements",
            tags=["Vendor - Partnership Agreements"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/my-agreement",
                self._get_my_agreement,
                {"response_model": VendorMyAgreementResponseSchema},
            ),
            (
                "get",
                "/download",
                self._download_my_agreement,
                {"response_model": None},
            ),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_my_agreement(
        self,
        current_user: CurrentUser = Depends(get_current_user),
        use_case: GetMyVendorAgreementUseCase = Depends(get_my_vendor_agreement_use_case),
    ):
        data = await use_case.execute(current_user)
        return self.build_response(
            message="Vendor agreement retrieved successfully.",
            data=data,
        )

    @handle_api_exceptions
    async def _download_my_agreement(
        self,
        current_user: CurrentUser = Depends(get_current_user),
        agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
    ):
        agreement = await agreement_service.repository.get_latest_by_vendor_id(current_user.id)
        if not agreement:
            raise AppException(
                status_code=404,
                message="No agreement found for this host account.",
                error_code="AGREEMENT_NOT_FOUND",
            )

        if agreement.pdf_file_url:
            try:
                data, content_type = await agreement_service.storage_service.get_object_bytes(agreement.pdf_file_url)
                if data:
                    filename = f"Host_Agreement_{agreement.public_id}.pdf"
                    return Response(
                        content=data,
                        media_type="application/pdf",
                        headers={
                            "Content-Disposition": f'inline; filename="{filename}"',
                            "Cache-Control": "private, max-age=3600",
                        },
                    )
            except Exception:
                pass

        url = await agreement_service.get_download_url(agreement)
        if not url:
            raise AppException(
                status_code=404,
                message="Executed agreement PDF not found or not yet signed.",
                error_code="PDF_NOT_FOUND",
            )

        return RedirectResponse(url=url)


controller = VendorAgreementController()
router = controller.router

