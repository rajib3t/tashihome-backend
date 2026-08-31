from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.dashboards.vendor_dashboard import VendorDashboardQueryDTO
from app.application.use_case.vendor.dashboard.get_vendor_dashboard_use_case import (
    GetVendorDashboardUseCase,
    GetVendorSummaryUseCase,
)
from app.deps.dashboard import (
    get_vendor_dashboard_use_case,
    get_vendor_summary_use_case,
)
from app.schemas.dashboard_schema import (
    VendorDashboardResponseSchema,
    VendorSummaryResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class VendorDashboardController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/dashboard",
            tags=["Vendor - Dashboard"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "", self._get_dashboard, {"response_model": VendorDashboardResponseSchema}),
            ("get", "/", self._get_dashboard, {"response_model": VendorDashboardResponseSchema, "include_in_schema": False}),
            ("get", "/summary", self._get_summary, {"response_model": VendorSummaryResponseSchema}),
        ]
        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)

    @handle_api_exceptions
    async def _get_dashboard(
        self,
        params: VendorDashboardQueryDTO = Depends(),
        use_case: GetVendorDashboardUseCase = Depends(get_vendor_dashboard_use_case),
    ):
        data = await use_case.execute(params)
        return self.build_response(
            message="Vendor dashboard data retrieved successfully.",
            data=data,
        )

    @handle_api_exceptions
    async def _get_summary(
        self,
        use_case: GetVendorSummaryUseCase = Depends(get_vendor_summary_use_case),
    ):
        data = await use_case.execute()
        return self.build_response(
            message="Vendor summary data retrieved successfully.",
            data=data,
        )


controller = VendorDashboardController()
router = controller.router

