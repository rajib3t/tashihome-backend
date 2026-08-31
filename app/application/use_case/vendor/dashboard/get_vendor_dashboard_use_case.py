from typing import Any, Dict

from app.application.dto.dashboards.vendor_dashboard import VendorDashboardQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.services.dashboard_service import DashboardService


class GetVendorDashboardUseCase(BaseUseCase):
    def __init__(self, dashboard_service: DashboardService, current_user: CurrentUser):
        self.dashboard_service = dashboard_service
        self.current_user = current_user

    async def execute(self, params: VendorDashboardQueryDTO) -> Dict[str, Any]:
        return await self.dashboard_service.get_vendor_dashboard(
            vendor_id=self.current_user.id,
            months=params.months,
        )


class GetVendorSummaryUseCase(BaseUseCase):
    def __init__(self, dashboard_service: DashboardService, current_user: CurrentUser):
        self.dashboard_service = dashboard_service
        self.current_user = current_user

    async def execute(self) -> Dict[str, Any]:
        return await self.dashboard_service.get_vendor_summary(
            vendor_id=self.current_user.id,
        )

