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


__all__ = [
    "BaseJob",
    "register_job",
    "get_job",
    "get_all_jobs",
    "run_job_by_name",
    "scheduler_manager",
    "start_scheduler",
    "stop_scheduler",
]

