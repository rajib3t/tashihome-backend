from fastapi import APIRouter, Depends, Query
from app.api.base_controller import BaseController
from app.application.dto.tax import TaxCreateDTO, TaxQueryDTO, TaxStatusUpdateDTO, TaxUpdateDTO
from app.application.use_case.admin.tax.create_tax_use_case import CreateTaxUseCase
from app.application.use_case.admin.tax.delete_tax_use_case import DeleteTaxUseCase
from app.application.use_case.admin.tax.get_tax_use_case import GetTaxUseCase, ListTaxesUseCase
from app.application.use_case.admin.tax.update_tax_use_case import UpdateTaxStatusUseCase, UpdateTaxUseCase
from app.deps.tax import (
    get_create_tax_use_case,
    get_delete_tax_use_case,
    get_get_tax_use_case,
    get_list_taxes_use_case,
    get_update_tax_status_use_case,
    get_update_tax_use_case,
)
from app.schemas.tax_schema import TaxListResponseSchema, TaxResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class TaxController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/taxes",
            tags=["Admin - Taxes"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._list_taxes, {"response_model": TaxListResponseSchema}),
            ("post", "/", self._create_tax, {"response_model": TaxResponseSchema, "status_code": 201}),
            ("get", "/{tax_id}", self._get_tax, {"response_model": TaxResponseSchema}),
            ("put", "/{tax_id}", self._update_tax, {"response_model": TaxResponseSchema}),
            ("patch", "/{tax_id}/status", self._update_tax_status, {"response_model": TaxResponseSchema}),
            ("delete", "/{tax_id}", self._delete_tax, {}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _list_taxes(
        self,
        params: TaxQueryDTO = Depends(),
        use_case: ListTaxesUseCase = Depends(get_list_taxes_use_case),
    ):
        page_result = await use_case.execute(params)
        return self.build_response(
            message="Taxes retrieved successfully.",
            data=page_result.items,
            meta=self.pagination_meta(page_result),
        )

    @handle_api_exceptions
    async def _get_tax(
        self,
        tax_id: str,
        use_case: GetTaxUseCase = Depends(get_get_tax_use_case),
    ):
        tax = await use_case.execute(tax_id)
        return self.build_response(
            message="Tax retrieved successfully.",
            data=tax,
        )

    @handle_api_exceptions
    async def _create_tax(
        self,
        data: TaxCreateDTO,
        use_case: CreateTaxUseCase = Depends(get_create_tax_use_case),
    ):
        tax = await use_case.execute(data)
        return self.build_response(
            message="Tax created successfully.",
            data=tax,
        )

    @handle_api_exceptions
    async def _update_tax(
        self,
        tax_id: str,
        data: TaxUpdateDTO,
        use_case: UpdateTaxUseCase = Depends(get_update_tax_use_case),
    ):
        tax = await use_case.execute(tax_id, data)
        return self.build_response(
            message="Tax updated successfully.",
            data=tax,
        )

    @handle_api_exceptions
    async def _update_tax_status(
        self,
        tax_id: str,
        data: TaxStatusUpdateDTO,
        use_case: UpdateTaxStatusUseCase = Depends(get_update_tax_status_use_case),
    ):
        tax = await use_case.execute(tax_id, data.status)
        return self.build_response(
            message="Tax status updated successfully.",
            data=tax,
        )

    @handle_api_exceptions
    async def _delete_tax(
        self,
        tax_id: str,
        hard: bool = Query(False, description="Perform permanent delete if true, otherwise deactivate"),
        use_case: DeleteTaxUseCase = Depends(get_delete_tax_use_case),
    ):
        await use_case.execute(tax_id, hard_delete=hard)
        return self.build_response(
            message="Tax deleted successfully.",
            data=None,
        )


controller = TaxController()
router = controller.router

