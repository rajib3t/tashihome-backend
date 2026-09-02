import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.dashboard_repository import DashboardRepository
from app.schedulers.base import BaseJob
from app.schedulers.registry import register_job

logger = logging.getLogger(__name__)

try:
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    IntervalTrigger = None


@register_job
class PublicStatsJob(BaseJob):
    name = "update_public_stats"
    description = "Refresh public statistics cache in database for fast API responses"
    lock_ttl_seconds = 180  # 3 minutes

    @property
    def trigger(self) -> Any:
        interval_minutes = getattr(settings, "PUBLIC_STATS_UPDATE_INTERVAL_MINUTES", 15)
        if IntervalTrigger is not None:
            return IntervalTrigger(minutes=interval_minutes)
        # Fallback trigger specification representation if APScheduler not installed
        return {"trigger": "interval", "minutes": interval_minutes}

    async def run(self, session: AsyncSession) -> Dict[str, Any]:
        repository = DashboardRepository(session)
        result = await repository.refresh_public_stats(key="overview")
        logger.info(
            "Updated public stats: homes=%s, destinations=%s, avg_rating=%s, reviews=%s",
            result.get("total_homes"),
            result.get("total_destinations"),
            result.get("average_rating"),
            result.get("total_reviews"),
        )
        return result

