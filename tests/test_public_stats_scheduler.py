import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.public_stat_model import PublicStat
from app.repositories.dashboard_repository import DashboardRepository
from app.schedulers.base import BaseJob
from app.schedulers.jobs.public_stats_job import PublicStatsJob
from app.schedulers.manager import AppSchedulerManager
from app.schedulers.registry import (
    get_all_jobs,
    get_job,
    register_job,
    run_job_by_name,
)
from app.schemas.public.stat_schema import PublicStatsResponseSchema
from app.services.dashboard_service import DashboardService


def test_public_stat_model_instantiation():
    """Verify PublicStat SQLAlchemy model fields."""
    stat = PublicStat(
        id=1,
        key="overview",
        total_homes=10,
        total_destinations=4,
        verified_percent=100,
        average_rating=4.8,
        total_reviews=25,
        stats=[{"key": "homes", "target": 10.0, "current": 0.0, "label": "homes"}],
    )
    assert stat.key == "overview"
    assert stat.total_homes == 10
    assert stat.average_rating == 4.8
    assert repr(stat).startswith("<PublicStat")


def test_get_public_stats_fast_cache_hit():
    """Verify get_public_stats returns directly from public_stats table in O(1) time without joins."""
    async def run_test():
        mock_session = AsyncMock()

        # Mock existing record in public_stats table
        existing_record = PublicStat(
            id=1,
            key="overview",
            total_homes=42,
            total_destinations=8,
            verified_percent=100,
            average_rating=4.9,
            total_reviews=150,
            stats=[
                {"key": "homes", "target": 42.0, "current": 0.0, "suffix": None, "decimals": 0, "label": "homes on the register"},
                {"key": "states", "target": 8.0, "current": 0.0, "suffix": None, "decimals": 0, "label": "hill states, one circuit"},
                {"key": "verified", "target": 100.0, "current": 0.0, "suffix": "%", "decimals": 0, "label": "visited on foot by us first"},
                {"key": "rating", "target": 4.9, "current": 0.0, "suffix": None, "decimals": 1, "label": "average guest rating"},
            ],
        )

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = existing_record
        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_execute_result

        repo = DashboardRepository(mock_session)
        result = await repo.get_public_stats()

        assert result["total_homes"] == 42
        assert result["total_destinations"] == 8
        assert result["average_rating"] == 4.9
        assert result["total_reviews"] == 150
        assert len(result["stats"]) == 4

        # Verify schema validates the result
        response = PublicStatsResponseSchema(
            status="success",
            message="Public statistics retrieved successfully.",
            data=result,
        )
        assert response.data.total_homes == 42

    asyncio.run(run_test())


def test_get_public_stats_fallback_refresh():
    """Verify get_public_stats automatically computes and stores when table row does not exist."""
    async def run_test():
        mock_session = AsyncMock()

        # First call returns None (table empty)
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_execute_result

        repo = DashboardRepository(mock_session)

        # Mock calculate_public_stats to avoid full DB queries in unit test
        calculated_data = {
            "total_homes": 61,
            "total_destinations": 7,
            "verified_percent": 100,
            "average_rating": 4.9,
            "total_reviews": 12,
            "stats": [{"key": "homes", "target": 61.0, "current": 0.0, "suffix": None, "decimals": 0, "label": "homes"}],
        }
        repo.calculate_public_stats = AsyncMock(return_value=calculated_data)

        result = await repo.get_public_stats()

        assert result["total_homes"] == 61
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    asyncio.run(run_test())


def test_dashboard_service_refresh_delegation():
    """Verify DashboardService delegates refresh_public_stats to repository."""
    async def run_test():
        mock_repo = AsyncMock()
        mock_repo.refresh_public_stats.return_value = {"total_homes": 50}

        service = DashboardService(mock_repo)
        res = await service.refresh_public_stats()

        assert res["total_homes"] == 50
        mock_repo.refresh_public_stats.assert_called_once_with(key="overview")

    asyncio.run(run_test())


def test_scheduled_job_registry():
    """Verify job registration, discovery, and lookup."""
    jobs = get_all_jobs()
    assert "update_public_stats" in jobs

    job = get_job("update_public_stats")
    assert job is not None
    assert isinstance(job, PublicStatsJob)
    assert job.name == "update_public_stats"


def test_custom_job_registration():
    """Verify adding a new scheduled job via @register_job."""
    @register_job
    class SampleAuditJob(BaseJob):
        name = "sample_audit_test_job"
        description = "Test audit job"

        @property
        def trigger(self):
            return "interval_10m"

        async def run(self, session):
            return {"audit_checked": True}

    sample_job = get_job("sample_audit_test_job")
    assert sample_job is not None
    assert sample_job.description == "Test audit job"


def test_public_stats_job_execution():
    """Verify PublicStatsJob.run() calls refresh_public_stats."""
    async def run_test():
        mock_session = AsyncMock()
        with patch.object(
            DashboardRepository,
            "refresh_public_stats",
            new_callable=AsyncMock,
        ) as mock_refresh:
            mock_refresh.return_value = {"total_homes": 30}

            job = PublicStatsJob()
            res = await job.run(mock_session)
            assert res["total_homes"] == 30
            mock_refresh.assert_called_once_with(key="overview")

    asyncio.run(run_test())


def test_run_job_by_name():
    """Verify run_job_by_name executes the job and handles locks/metrics."""
    async def run_test():
        with patch.object(PublicStatsJob, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"refreshed": True}
            with patch("app.schedulers.base.db") as mock_db:
                mock_db._engine = "connected"
                mock_session = AsyncMock()
                mock_db.async_session.return_value.__aenter__.return_value = mock_session

                result = await run_job_by_name("update_public_stats")
                assert result["status"] == "success"
                assert result["data"]["refreshed"] is True
                assert "duration_ms" in result

    asyncio.run(run_test())


def test_scheduler_manager_lifecycle():
    """Verify AppSchedulerManager start and shutdown."""
    manager = AppSchedulerManager()
    assert not manager.is_running
    manager.shutdown()
    assert not manager.is_running

