import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from app.core.redis import redis_client

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    name: str
    payload: dict[str, Any]
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps(
            {
                "name": self.name,
                "occurred_at": self.occurred_at,
                "payload": self.payload,
            },
            default=str,
        )


class EventBus:
    async def publish(self, event: DomainEvent) -> None:
        raise NotImplementedError("EventBus.publish must be implemented")


class RedisEventBus(EventBus):
    def __init__(self, stream_name: str = "app:events:stream"):
        self.redis = redis_client
        self.stream_name = stream_name

    async def publish(self, event: DomainEvent) -> None:
        if self.redis.client is None:
            logger.warning("Skipping event publish because Redis is not connected: %s", event.name)
            return

        try:
            # XADD pushes message to Redis Stream
            # maxlen=10000 ensures stream size is kept bounded
            await self.redis.client.xadd(
                self.stream_name,
                {
                    "event_name": event.name,
                    "event_data": event.to_json(),
                },
                maxlen=10000,
                approximate=True,
            )
            logger.debug("Published event %s to stream %s", event.name, self.stream_name)
        except Exception as exc:
            logger.error("Failed to publish event %s to Redis Stream: %s", event.name, exc)


class RedisEventSubscriber:
    """
    Redis Stream Consumer with Consumer Groups.
    Using Consumer Groups ensures each event is delivered to EXACTLY ONE worker,
    eliminating duplicate events and duplicate emails across multiple workers.
    """

    def __init__(
        self,
        stream_name: str = "app:events:stream",
        group_name: str = "app:events:group",
    ):
        self.redis = redis_client
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = f"worker_{os.getpid()}_{uuid.uuid4().hex[:6]}"
        self._running = False

    async def _ensure_group(self) -> None:
        """Create consumer group if it doesn't already exist."""
        try:
            await self.redis.client.xgroup_create(
                name=self.stream_name,
                groupname=self.group_name,
                id="$",
                mkstream=True,
            )
            logger.info("Created Redis stream group '%s' on '%s'", self.group_name, self.stream_name)
        except Exception as exc:
            # BUSYGROUP error means group already exists, which is expected across multiple workers
            if "BUSYGROUP" in str(exc):
                pass
            else:
                logger.warning("Warning ensuring consumer group '%s': %s", self.group_name, exc)

    async def listen(
        self,
        handlers: dict[str, Callable[[dict[str, Any]], Awaitable[None]]],
        block_ms: int = 2000,
    ) -> None:
        if self.redis.client is None:
            raise RuntimeError("Redis client is not connected")

        await self._ensure_group()
        self._running = True
        logger.info(
            "Event subscriber consumer %s started listening on group %s",
            self.consumer_name,
            self.group_name,
        )

        try:
            while self._running:
                try:
                    # ">" means only new messages that have never been delivered to another consumer in this group
                    stream_entries = await self.redis.client.xreadgroup(
                        groupname=self.group_name,
                        consumername=self.consumer_name,
                        streams={self.stream_name: ">"},
                        count=5,
                        block=block_ms,
                    )

                    if not stream_entries:
                        await asyncio.sleep(0.05)
                        continue

                    for stream_name, messages in stream_entries:
                        for message_id, data in messages:
                            await self._handle_message(message_id, data, handlers)

                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logger.error("Error reading from Redis Stream %s: %s", self.stream_name, exc)
                    await asyncio.sleep(1.0)
        finally:
            await self.close()

    async def _handle_message(
        self,
        message_id: str,
        data: dict[str, Any],
        handlers: dict[str, Callable[[dict[str, Any]], Awaitable[None]]],
    ) -> None:
        event_name = data.get("event_name")
        raw_event_data = data.get("event_data")

        if not event_name or not raw_event_data:
            await self._ack(message_id)
            return

        try:
            event_dict = json.loads(raw_event_data)
            payload = event_dict.get("payload", {})
        except Exception:
            logger.error("Invalid JSON payload in stream message %s", message_id)
            await self._ack(message_id)
            return

        handler = handlers.get(event_name)
        if handler:
            try:
                await handler(payload)
            except Exception as exc:
                logger.exception("Error executing handler for event %s (message %s): %s", event_name, message_id, exc)
        else:
            logger.warning("No handler registered for event %s", event_name)

        await self._ack(message_id)

    async def _ack(self, message_id: str) -> None:
        """Acknowledge message so it won't be processed again."""
        try:
            if self.redis.client:
                await self.redis.client.xack(self.stream_name, self.group_name, message_id)
        except Exception as exc:
            logger.error("Failed to ACK message %s: %s", message_id, exc)

    async def close(self) -> None:
        self._running = False