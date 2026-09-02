"""Scheduled Jobs Package.

Import all job implementations here to ensure they are registered with the central registry.
To add a new scheduled function:
1. Create a new job file in this directory inheriting from BaseJob with @register_job
2. Import the job class here.
"""

from app.schedulers.jobs.public_stats_job import PublicStatsJob

__all__ = [
    "PublicStatsJob",
]

