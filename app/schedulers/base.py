from abc import ABC, abstractmethod
import asyncio
import logging
import time
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class BaseJob(ABC):
    """
    Base class for all enterprise scheduled jobs.

    Provides:
    - Standard lifecycle (execute wrapper with logging & metrics)
    - Redis distributed lock support to prevent overlapping runs
    - Database session lifecycle management
    - Standard error handling
    """

    name: str = "base_job"
    description: str = "Base scheduled job"
    lock_ttl_seconds: int = 300  # 5 minutes default lock

    @property
    @abstractmethod
    def trigger(self) -> Any:
        """Return the APScheduler trigger (IntervalTrigger, CronTrigger, etc.)."""
        pass

    async def execute(self) -> Dict[str, Any]:
        """
        Executes the job with distributed locking, logging, and error handling.
        """
        lock_key = f"lock:scheduler_job:{self.name}"
        lock_acquired = False
        start_time = time.time()

        # Attempt to acquire distributed lock via Redis if connected
        if redis_client.client:
            try:
                lock_acquired = await redis_client.client.set(
                    lock_key, "locked", ex=self.lock_ttl_seconds, nx=True
                )
                if not lock_acquired:
                    logger.info(
                        "Job '%s' skipped: already in progress on another worker/instance",
                        self.name,
                    )
                    return {
                        "status": "skipped",
                        "reason": "lock_held",
                        "duration_ms": 0,
                    }
            except Exception as e:
                logger.warning("Redis lock error for job '%s': %s. Continuing anyway.", self.name, e)

        logger.info("Starting scheduled job: %s (%s)", self.name, self.description)

        try:
            # Ensure database is connected if called from standalone runner
            if db._engine is None:
                db.connect()

            async with db.async_session() as session:
                result = await self.run(session)

            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.info(
                "Completed scheduled job '%s' successfully in %sms",
                self.name,
                duration_ms,
            )
            return {
                "status": "success",
                "duration_ms": duration_ms,
                "data": result,
            }

        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "Job '%s' failed after %sms with error: %s",
                self.name,
                duration_ms,
                e,
                exc_info=True,
            )
            return {
                "status": "failed",
                "error": str(e),
                "duration_ms": duration_ms,
            }

        finally:
            if lock_acquired and redis_client.client:
                try:
                    await redis_client.client.delete(lock_key)
                except Exception:
                    pass

    @abstractmethod
    async def run(self, session: AsyncSession) -> Any:
        """Implement the job's core logic here."""
        pass

