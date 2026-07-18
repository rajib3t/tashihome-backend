import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Create a Redis connection and verify it with PING."""
        if self.client:
            return

        try:
            self.client = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            await self.client.ping()
            logger.info("Connected to Redis")

        except Exception:
            logger.exception("Unable to connect to Redis")
            await self.close()
            raise

    async def close(self) -> None:
        """Close the Redis connection."""
        if self.client:
            await self.client.aclose()  # redis-py >= 5.x
            self.client = None
            logger.info("Redis connection closed")


redis_client = RedisClient()