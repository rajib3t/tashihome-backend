from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.dashboards.admin_dashboard import AdminDashboardQueryDTO
from app.application.use_case.admin.dashboard.get_admin_dashboard_use_case import (
    GetAdminDashboardUseCase,
    GetAdminSummaryUseCase,
)
from app.deps.dashboard import (
    get_admin_dashboard_use_case,
    get_admin_summary_use_case,
)
from app.schemas.dashboard_schema import (
    AdminDashboardResponseSchema,
    AdminSummaryResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class AdminDashboardController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/dashboard",
            tags=["Admin - Dashboard"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "", self._get_dashboard, {"response_model": AdminDashboardResponseSchema}),
            ("get", "/", self._get_dashboard, {"response_model": AdminDashboardResponseSchema, "include_in_schema": False}),
            ("get", "/summary", self._get_summary, {"response_model": AdminSummaryResponseSchema}),
        ]
        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)

    @handle_api_exceptions
    async def _get_dashboard(
        self,
        params: AdminDashboardQueryDTO = Depends(),
        use_case: GetAdminDashboardUseCase = Depends(get_admin_dashboard_use_case),
    ):
        data = await use_case.execute(params)
        return self.build_response(
            message="Admin dashboard data retrieved successfully.",
            data=data,
        )

    @handle_api_exceptions
    async def _get_summary(
        self,
        use_case: GetAdminSummaryUseCase = Depends(get_admin_summary_use_case),
    ):
        data = await use_case.execute()
        return self.build_response(
            message="Admin summary data retrieved successfully.",
            data=data,
        )


controller = AdminDashboardController()
router = controller.router

