import logging
from typing import Callable, Dict, List, Optional, Type, Union

from app.schedulers.base import BaseJob

logger = logging.getLogger(__name__)

_JOB_REGISTRY: Dict[str, BaseJob] = {}


def register_job(job_or_class: Union[BaseJob, Type[BaseJob]]) -> Union[BaseJob, Type[BaseJob]]:
    """
    Decorator or function to register a scheduled job in the central registry.
    Can be applied to a BaseJob subclass or an instance of BaseJob.
    """
    if isinstance(job_or_class, type) and issubclass(job_or_class, BaseJob):
        instance = job_or_class()
    elif isinstance(job_or_class, BaseJob):
        instance = job_or_class
    else:
        raise TypeError(f"Expected BaseJob subclass or instance, got {type(job_or_class)}")

    if instance.name in _JOB_REGISTRY:
        logger.warning("Overwriting existing scheduled job registration for '%s'", instance.name)

    _JOB_REGISTRY[instance.name] = instance
    logger.debug("Registered scheduled job '%s'", instance.name)
    return job_or_class


def get_job(name: str) -> Optional[BaseJob]:
    """Retrieve a registered job by its unique name."""
    return _JOB_REGISTRY.get(name)


def get_all_jobs() -> Dict[str, BaseJob]:
    """Retrieve all registered jobs."""
    return dict(_JOB_REGISTRY)


async def run_job_by_name(name: str) -> Dict[str, any]:
    """Run a specific job by name directly."""
    job = get_job(name)
    if not job:
        raise ValueError(f"Job '{name}' not found in registry. Registered jobs: {list(_JOB_REGISTRY.keys())}")
    return await job.execute()

