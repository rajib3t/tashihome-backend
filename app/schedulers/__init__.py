from app.schedulers.base import BaseJob
from app.schedulers.manager import scheduler_manager
from app.schedulers.registry import (
    get_all_jobs,
    get_job,
    register_job,
    run_job_by_name,
)
import app.schedulers.jobs  # noqa: F401


def start_scheduler() -> None:
    """Start the APScheduler manager."""
    scheduler_manager.start()


def stop_scheduler(wait: bool = False) -> None:
    """Stop the APScheduler manager."""
    scheduler_manager.shutdown(wait=wait)


async def trigger_job(name: str):
    """Trigger immediate execution of a registered job."""
    return await scheduler_manager.trigger_job(name)


__all__ = [
    "BaseJob",
    "register_job",
    "get_job",
    "get_all_jobs",
    "run_job_by_name",
    "trigger_job",
    "scheduler_manager",
    "start_scheduler",
    "stop_scheduler",
]

