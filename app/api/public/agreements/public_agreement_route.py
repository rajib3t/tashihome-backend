from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.api.base_controller import BaseController
from app.application.dto.agreements.agreement_dto import SignAgreementDTO
from app.application.use_case.public.agreements.get_public_agreement_use_case import (
    GetPublicAgreementUseCase,
)
from app.application.use_case.public.agreements.sign_agreement_use_case import (
    SignAgreementUseCase,
)
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser, get_optional_current_user
from app.deps.agreement import (
    get_public_agreement_use_case,
    get_sign_agreement_use_case,
)
from app.deps.service import get_vendor_agreement_service
from app.schemas.vendor_agreement_schema import PublicAgreementResponseSchema
from app.services.vendor_agreement_service import VendorAgreementService
from app.utils.exception_decorate import handle_api_exceptions


class PublicAgreementController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/agreements",
            tags=["Public - Host Agreements & E-Sign"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/{token}", self._get_agreement, {"response_model": PublicAgreementResponseSchema}),
            ("post", "/{token}/sign", self._sign_agreement, {"response_model": PublicAgreementResponseSchema}),
            ("get", "/{token}/pdf", self._download_pdf, {"response_model": None}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_agreement(
        self,
        token: str,
        use_case: GetPublicAgreementUseCase = Depends(get_public_agreement_use_case),
    ):
        data = await use_case.execute(token)
        return self.build_response(
            message="Agreement retrieved successfully.",
            data=data,
        )

    @handle_api_exceptions
    async def _sign_agreement(
        self,
        token: str,
        data: SignAgreementDTO,
        request: Request,
        current_user: CurrentUser | None = Depends(get_optional_current_user),
        use_case: SignAgreementUseCase = Depends(get_sign_agreement_use_case),
    ):
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        result = await use_case.execute(
            token=token,
            sign_dto=data,
            client_ip=client_ip,
            user_agent=user_agent,
            current_user=current_user,
        )
        return self.build_response(
            message="Host agreement signed and executed successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _download_pdf(
        self,
        token: str,
        agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
    ):
        agreement = await agreement_service.get_by_token(token)
        url = await agreement_service.get_download_url(agreement)
        if not url:
            raise AppException(
                status_code=404,
                message="Executed agreement PDF not found or not yet signed.",
                error_code="PDF_NOT_FOUND",
            )
        return RedirectResponse(url=url)


controller = PublicAgreementController()
router = controller.router

