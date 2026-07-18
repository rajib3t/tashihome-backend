import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

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
    def __init__(self):
        self.redis = redis_client

    async def publish(self, event: DomainEvent) -> None:
        if self.redis.client is None:
            logger.warning("Skipping event publish because Redis is not connected: %s", event.name)
            return

        await self.redis.client.publish(event.name, event.to_json())


class RedisEventSubscriber:
    def __init__(self):
        self.redis = redis_client
        self.pubsub = None
        self._running = False

    async def listen(self, handlers: dict[str, Callable[[dict[str, Any]], Awaitable[None]]], timeout: float = 1.0) -> None:
        if self.redis.client is None:
            raise RuntimeError("Redis client is not connected")

        self.pubsub = self.redis.client.pubsub()
        await self.pubsub.subscribe(*handlers.keys())
        self._running = True

        try:
            while self._running:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=timeout)
                if message is None:
                    await asyncio.sleep(0.1)
                    continue

                if message.get("type") != "message":
                    continue

                channel = message.get("channel")
                raw_data = message.get("data")
                if raw_data is None:
                    continue

                payload = raw_data
                if isinstance(payload, (bytes, bytearray)):
                    payload = payload.decode("utf-8")

                try:
                    event_data = json.loads(payload)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in Redis event on channel %s", channel)
                    continue

                handler = handlers.get(channel)
                if not handler:
                    logger.warning("No handler registered for Redis event channel %s", channel)
                    continue

                try:
                    await handler(event_data.get("payload", {}))
                except Exception as exc:
                    logger.exception("Error handling Redis event %s: %s", channel, exc)
        finally:
            await self.close()

    async def close(self) -> None:
        self._running = False
        if self.pubsub is not None:
            try:
                await self.pubsub.unsubscribe()
            except Exception:
                pass
            try:
                await self.pubsub.close()
            except Exception:
                pass
            self.pubsub = None