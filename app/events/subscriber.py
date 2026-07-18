import asyncio
import json
import logging
from typing import Awaitable, Callable

from app.core.events import RedisEventSubscriber

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict], Awaitable[None]]

HANDLERS: dict[str, EventHandler] = {
    
}


async def start_event_subscriber() -> None:
    subscriber = RedisEventSubscriber()
    await subscriber.listen(HANDLERS)