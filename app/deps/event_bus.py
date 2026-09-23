from app.core.events import RedisEventBus

# Module-level singleton — shares the same redis_client connection pool
# across all requests rather than creating a new object per request.
# RedisEventBus itself is stateless (it holds only a reference to the
# shared redis_client), so a singleton is perfectly safe.
_event_bus: RedisEventBus | None = None


def get_event_bus() -> RedisEventBus:
    """
    Return the shared RedisEventBus singleton.

    Using a module-level instance ensures:
    - No per-request object allocation overhead.
    - Teardown / cleanup is handled by the application lifespan (redis_client.close()),
      not per-request FastAPI DI teardown.
    - Can safely be used with ``Depends(get_event_bus)`` in route dependencies.
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = RedisEventBus()
    return _event_bus