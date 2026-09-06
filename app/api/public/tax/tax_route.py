from fastapi import APIRouter, Depends
from app.api.base_controller import BaseController
from app.application.use_case.public.tax.get_public_taxes_use_case import GetDefaultTaxUseCase, GetPublicTaxesUseCase
from app.deps.tax import get_default_tax_use_case, get_public_taxes_use_case
from app.schemas.tax_schema import PublicTaxListResponseSchema, TaxResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class PublicTaxController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/taxes",
            tags=["Public - Taxes"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_taxes, {"response_model": PublicTaxListResponseSchema}),
            ("get", "/default", self._get_default_tax, {"response_model": TaxResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_taxes(
        self,
        use_case: GetPublicTaxesUseCase = Depends(get_public_taxes_use_case),
    ):
        taxes = await use_case.execute()
        return self.build_response(
            message="Active taxes retrieved successfully.",
            data=taxes,
        )

    @handle_api_exceptions
    async def _get_default_tax(
        self,
        use_case: GetDefaultTaxUseCase = Depends(get_default_tax_use_case),
    ):
        tax = await use_case.execute()
        return self.build_response(
            message="Default tax retrieved successfully.",
            data=tax,
        )


controller = PublicTaxController()
router = controller.router

