import asyncio
import logging
import os
import uuid
from typing import Awaitable, Callable, Optional

from app.core.redis import redis_client

logger = logging.getLogger(__name__)

EXTEND_LOCK_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
else
    return 0
end
"""

RELEASE_LOCK_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class RedisLeaderElector:
    """
    Continuous leader election for multi-worker deployments.
    - Continuously attempts to acquire or renew a distributed lock in Redis.
    - Exactly one worker is elected leader at any time and runs the event subscriber.
    - If the leader crashes or restarts, a standby worker automatically takes over when the TTL expires.
    - On graceful shutdown, the leader releases the lock immediately so another worker takes over instantly.
    """

    def __init__(
        self,
        lock_key: str = "lock:event_subscriber_leader",
        ttl_seconds: int = 10,
        heartbeat_interval: float = 3.0,
    ):
        self.redis = redis_client
        self.lock_key = lock_key
        self.ttl_seconds = ttl_seconds
        self.heartbeat_interval = heartbeat_interval
        self.worker_id = f"worker_{os.getpid()}_{uuid.uuid4().hex[:6]}"
        self.is_leader = False
        self._running = False
        self._subscriber_task: Optional[asyncio.Task] = None
        self._election_task: Optional[asyncio.Task] = None

    async def start(self, run_subscriber_func: Callable[[], Awaitable[None]]) -> None:
        """Start the continuous leader election background task."""
        self._running = True
        self._election_task = asyncio.create_task(self._election_loop(run_subscriber_func))

    async def _election_loop(self, run_subscriber_func: Callable[[], Awaitable[None]]) -> None:
        logger.info("Started leader election loop for %s", self.worker_id)
        while self._running:
            try:
                if not self.redis.client:
                    await asyncio.sleep(self.heartbeat_interval)
                    continue

                if self.is_leader:
                    # Renew existing lock
                    extended = await self.redis.client.eval(
                        EXTEND_LOCK_LUA,
                        1,
                        self.lock_key,
                        self.worker_id,
                        str(self.ttl_seconds),
                    )
                    if not extended:
                        logger.warning(
                            "Worker %s lost leadership lock; stepping down to standby",
                            self.worker_id,
                        )
                        await self._demote()
                    else:
                        # Ensure subscriber task is still running if we are leader
                        if self._subscriber_task is None or self._subscriber_task.done():
                            logger.info(
                                "Worker %s restarting subscriber task",
                                self.worker_id,
                            )
                            self._subscriber_task = asyncio.create_task(run_subscriber_func())
                else:
                    # Attempt to acquire leadership lock
                    acquired = await self.redis.client.set(
                        self.lock_key,
                        self.worker_id,
                        ex=self.ttl_seconds,
                        nx=True,
                    )
                    if acquired:
                        logger.info(
                            "Worker %s acquired leadership; starting event subscriber",
                            self.worker_id,
                        )
                        self.is_leader = True
                        self._subscriber_task = asyncio.create_task(run_subscriber_func())
                    else:
                        logger.debug("Worker %s is on standby (leader active)", self.worker_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in leader election loop for %s: %s", self.worker_id, e)
                if self.is_leader:
                    await self._demote()

            await asyncio.sleep(self.heartbeat_interval)

    async def _demote(self) -> None:
        """Demote this worker from leader to standby and stop the subscriber task."""
        self.is_leader = False
        if self._subscriber_task and not self._subscriber_task.done():
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
        self._subscriber_task = None

    async def stop(self) -> None:
        """Stop leader election loop and cleanly release the leadership lock."""
        self._running = False
        if self._election_task and not self._election_task.done():
            self._election_task.cancel()
            try:
                await self._election_task
            except asyncio.CancelledError:
                pass

        await self._demote()

        if self.redis.client:
            try:
                await self.redis.client.eval(
                    RELEASE_LOCK_LUA,
                    1,
                    self.lock_key,
                    self.worker_id,
                )
                logger.info("Worker %s released leadership lock", self.worker_id)
            except Exception as e:
                logger.warning("Error releasing leader lock on shutdown: %s", e)

