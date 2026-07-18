from app.core.events import RedisEventBus


async def get_event_bus() -> RedisEventBus:
    return RedisEventBus()