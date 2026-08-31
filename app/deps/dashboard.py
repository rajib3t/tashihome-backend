from fastapi import Depends

from app.application.use_case.admin.dashboard.get_admin_dashboard_use_case import (
    GetAdminDashboardUseCase,
    GetAdminSummaryUseCase,
)
from app.application.use_case.vendor.dashboard.get_vendor_dashboard_use_case import (
    GetVendorDashboardUseCase,
    GetVendorSummaryUseCase,
)
from app.deps.auth import CurrentUser, require_admin_or_staff, require_vendor
from app.deps.service import get_dashboard_service
from app.services.dashboard_service import DashboardService


async def get_admin_dashboard_use_case(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    _: CurrentUser = Depends(require_admin_or_staff),
) -> GetAdminDashboardUseCase:
    return GetAdminDashboardUseCase(dashboard_service=dashboard_service)


async def get_admin_summary_use_case(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    _: CurrentUser = Depends(require_admin_or_staff),
) -> GetAdminSummaryUseCase:
    return GetAdminSummaryUseCase(dashboard_service=dashboard_service)


async def get_vendor_dashboard_use_case(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> GetVendorDashboardUseCase:
    return GetVendorDashboardUseCase(
        dashboard_service=dashboard_service,
        current_user=current_user,
    )


async def get_vendor_summary_use_case(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> GetVendorSummaryUseCase:
    return GetVendorSummaryUseCase(
        dashboard_service=dashboard_service,
        current_user=current_user,
    )

