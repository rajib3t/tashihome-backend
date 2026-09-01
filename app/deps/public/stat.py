from fastapi import Depends

from app.application.use_case.public.stat.get_public_stats_use_case import GetPublicStatsUseCase
from app.deps.service import get_dashboard_service
from app.services.dashboard_service import DashboardService


async def get_public_stats_use_case(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> GetPublicStatsUseCase:
    return GetPublicStatsUseCase(dashboard_service=dashboard_service)

