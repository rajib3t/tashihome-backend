import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional

from app.schedulers.base import BaseJob
from app.schedulers.registry import get_all_jobs, get_job

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    AsyncIOScheduler = None


class AppSchedulerManager:
    """
    Enterprise Scheduler Manager.
    Manages the lifecycle of background scheduled tasks.
    Supports APScheduler AsyncIOScheduler with automatic fallback to native asyncio loops.
    """

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running: bool = False
        self._asyncio_tasks: List[asyncio.Task] = []

    @property
    def is_running(self) -> bool:
        """Check if scheduler (APScheduler or asyncio loop) is currently running."""
        if self._scheduler is not None and self._scheduler.running:
            return True
        return self._running and len(self._asyncio_tasks) > 0

    def start(self) -> None:
        """Start the scheduler and register all jobs from the central registry."""
        if self.is_running:
            logger.info("Scheduler is already running.")
            return

        # Ensure all registered jobs are imported and discovered
        import app.schedulers.jobs  # noqa: F401

        jobs = get_all_jobs()
        if not jobs:
            logger.warning("No jobs registered in scheduler registry.")
            return

        self._running = True

        if HAS_APSCHEDULER:
            self._start_apscheduler(jobs)
        else:
            self._start_asyncio_fallback(jobs)

    def _start_apscheduler(self, jobs: Dict[str, BaseJob]) -> None:
        """Initialize and start APScheduler AsyncIOScheduler."""
        try:
            self._scheduler = AsyncIOScheduler(timezone=timezone.utc)
            now = datetime.now(timezone.utc)

            for job_name, job_instance in jobs.items():
                try:
                    run_on_startup = getattr(job_instance, "run_on_startup", True)
                    kwargs = {
                        "func": job_instance.execute,
                        "trigger": job_instance.trigger,
                        "id": job_name,
                        "name": job_instance.description,
                        "replace_existing": True,
                        "max_instances": 1,
                        "coalesce": True,
                    }
                    if run_on_startup:
                        kwargs["next_run_time"] = now

                    self._scheduler.add_job(**kwargs)
                    logger.info(
                        "Scheduled job '%s' with trigger: %s (run_on_startup=%s)",
                        job_name,
                        job_instance.trigger,
                        run_on_startup,
                    )
                except Exception as e:
                    logger.error("Failed to schedule job '%s': %s", job_name, e, exc_info=True)

            self._scheduler.start()
            logger.info("AppScheduler (APScheduler) started with %d registered job(s)", len(jobs))
        except Exception as e:
            logger.error("Failed to start APScheduler, falling back to native asyncio runner: %s", e, exc_info=True)
            self._scheduler = None
            self._start_asyncio_fallback(jobs)

    def _start_asyncio_fallback(self, jobs: Dict[str, BaseJob]) -> None:
        """Fallback background task runner when APScheduler is unavailable."""
        logger.info("Starting background tasks using native asyncio fallback loop (%d job(s))", len(jobs))
        for job_name, job_instance in jobs.items():
            task = asyncio.create_task(
                self._run_job_loop(job_name, job_instance),
                name=f"scheduler_job_{job_name}",
            )
            self._asyncio_tasks.append(task)

    async def _run_job_loop(self, job_name: str, job_instance: BaseJob) -> None:
        """Continuous interval execution loop for native asyncio background execution."""
        run_on_startup = getattr(job_instance, "run_on_startup", True)
        interval = max(5, getattr(job_instance, "interval_seconds", 900))

        if not run_on_startup:
            await asyncio.sleep(interval)

        while self._running:
            try:
                await job_instance.execute()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error running scheduled job loop for '%s': %s", job_name, e, exc_info=True)

            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break

    async def trigger_job(self, job_name: str) -> Dict[str, any]:
        """Manually trigger immediate execution of a registered job."""
        job = get_job(job_name)
        if not job:
            raise ValueError(f"Job '{job_name}' not found in registry")
        return await job.execute()

    def shutdown(self, wait: bool = False) -> None:
        """Gracefully shut down the scheduler and any running background tasks."""
        self._running = False

        if self._scheduler and self._scheduler.running:
            logger.info("Shutting down APScheduler...")
            self._scheduler.shutdown(wait=wait)
        self._scheduler = None

        for task in self._asyncio_tasks:
            if not task.done():
                task.cancel()
        self._asyncio_tasks.clear()

        logger.info("AppScheduler shutdown complete.")


scheduler_manager = AppSchedulerManager()
