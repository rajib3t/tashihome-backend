from typing import Any, Dict

from app.application.use_case.base_use_case import BaseUseCase
from app.services.dashboard_service import DashboardService


class GetPublicStatsUseCase(BaseUseCase):
    def __init__(self, dashboard_service: DashboardService):
        self.dashboard_service = dashboard_service

    async def execute(self) -> Dict[str, Any]:
        return await self.dashboard_service.get_public_stats()

