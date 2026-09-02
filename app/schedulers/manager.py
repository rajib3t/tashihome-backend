import asyncio
import logging
from typing import Optional

from app.schedulers.registry import get_all_jobs

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    AsyncIOScheduler = None


class AppSchedulerManager:
    """
    Manages the lifecycle of APScheduler AsyncIOScheduler.
    """

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running: bool = False

    @property
    def is_running(self) -> bool:
        return self._running and self._scheduler is not None and self._scheduler.running

    def start(self) -> None:
        """Start the scheduler and register all jobs from the registry."""
        if not HAS_APSCHEDULER:
            logger.warning(
                "APScheduler is not installed in the environment. "
                "Scheduled tasks will not run. Run 'uv add apscheduler' or 'pip install apscheduler'."
            )
            return

        if self.is_running:
            logger.info("Scheduler is already running.")
            return

        # Ensure jobs are imported and discovered
        import app.schedulers.jobs  # noqa: F401

        self._scheduler = AsyncIOScheduler()

        jobs = get_all_jobs()
        for job_name, job_instance in jobs.items():
            try:
                self._scheduler.add_job(
                    job_instance.execute,
                    trigger=job_instance.trigger,
                    id=job_name,
                    name=job_instance.description,
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True,
                )
                logger.info("Scheduled job '%s' with trigger: %s", job_name, job_instance.trigger)
            except Exception as e:
                logger.error("Failed to schedule job '%s': %s", job_name, e, exc_info=True)

        self._scheduler.start()
        self._running = True
        logger.info("AppScheduler successfully started with %d registered job(s)", len(jobs))

    def shutdown(self, wait: bool = False) -> None:
        """Gracefully shut down the scheduler."""
        if self._scheduler and self._scheduler.running:
            logger.info("Shutting down AppScheduler...")
            self._scheduler.shutdown(wait=wait)
        self._running = False
        self._scheduler = None
        logger.info("AppScheduler shutdown complete.")


scheduler_manager = AppSchedulerManager()

