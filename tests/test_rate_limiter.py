import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings, settings
from app.core.exceptions import RateLimitExceededError
from app.core.rate_limiter import (
    RateLimiter,
    RateLimitMiddleware,
    RateLimitResult,
    RedisRateLimiter,
    get_client_ip,
)


def test_rate_limit_settings_defaults():
    s = Settings(
        APP_NAME="Test",
        DATABASE_URL="postgresql://test:test@localhost:5432/test",
        JWT_SECRET="secret",
    )
    assert s.RATE_LIMIT_ENABLED is True
    assert s.RATE_LIMIT_COOLDOWN_SECONDS == 3600
    assert s.RATE_LIMIT_GET_MAX_REQUESTS == 120
    assert s.RATE_LIMIT_POST_MAX_REQUESTS == 30
    assert s.RATE_LIMIT_PUT_MAX_REQUESTS == 30
    assert s.RATE_LIMIT_PATCH_MAX_REQUESTS == 30
    assert s.RATE_LIMIT_DELETE_MAX_REQUESTS == 20
    assert s.RATE_LIMIT_DEFAULT_MAX_REQUESTS == 60

    assert s.get_rate_limit_for_method("GET") == (120, 60)
    assert s.get_rate_limit_for_method("POST") == (30, 60)
    assert s.get_rate_limit_for_method("PUT") == (30, 60)
    assert s.get_rate_limit_for_method("PATCH") == (30, 60)
    assert s.get_rate_limit_for_method("DELETE") == (20, 60)
    assert s.get_rate_limit_for_method("OPTIONS") == (60, 60)


def test_rate_limit_settings_custom_override():
    s = Settings(
        APP_NAME="Test",
        DATABASE_URL="postgresql://test:test@localhost:5432/test",
        JWT_SECRET="secret",
        RATE_LIMIT_COOLDOWN_SECONDS=7200,
        RATE_LIMIT_GET_MAX_REQUESTS=200,
        RATE_LIMIT_GET_WINDOW_SECONDS=120,
        RATE_LIMIT_POST_MAX_REQUESTS=10,
        RATE_LIMIT_POST_WINDOW_SECONDS=30,
    )
    assert s.RATE_LIMIT_COOLDOWN_SECONDS == 7200
    assert s.get_rate_limit_for_method("GET") == (200, 120)
    assert s.get_rate_limit_for_method("POST") == (10, 30)


def test_get_client_ip_headers():
    # 1. X-Forwarded-For with multiple IPs
    req = MagicMock(spec=Request)
    req.headers = {"x-forwarded-for": "203.0.113.195, 70.41.3.18, 150.172.238.178"}
    req.client = MagicMock(host="10.0.0.1")
    assert get_client_ip(req) == "203.0.113.195"

    # 2. X-Real-IP
    req2 = MagicMock(spec=Request)
    req2.headers = {"x-real-ip": "198.51.100.2"}
    req2.client = MagicMock(host="10.0.0.1")
    assert get_client_ip(req2) == "198.51.100.2"

    # 3. Direct client host
    req3 = MagicMock(spec=Request)
    req3.headers = {}
    req3.client = MagicMock(host="192.168.1.50")
    assert get_client_ip(req3) == "192.168.1.50"

    # 4. Fallback
    req4 = MagicMock(spec=Request)
    req4.headers = {}
    req4.client = None
    assert get_client_ip(req4) == "127.0.0.1"


def test_rate_limiter_disabled():
    async def run_test():
        limiter = RedisRateLimiter()
        req = MagicMock(spec=Request)
        req.method = "GET"
        req.headers = {}
        req.client = MagicMock(host="1.2.3.4")

        orig = settings.RATE_LIMIT_ENABLED
        try:
            settings.RATE_LIMIT_ENABLED = False
            result = await limiter.check(req)
            assert result.is_allowed is True
            assert result.remaining == 120
            assert result.retry_after == 0
            assert result.in_cooldown is False
        finally:
            settings.RATE_LIMIT_ENABLED = orig

    asyncio.run(run_test())


def test_rate_limiter_redis_none():
    async def run_test():
        limiter = RedisRateLimiter()
        limiter.redis = MagicMock()
        limiter.redis.client = None

        req = MagicMock(spec=Request)
        req.method = "POST"
        req.headers = {}
        req.client = MagicMock(host="1.2.3.4")

        result = await limiter.check(req)
        assert result.is_allowed is True
        assert result.method == "POST"
        assert result.limit == 30

    asyncio.run(run_test())


def test_rate_limiter_in_cooldown():
    async def run_test():
        limiter = RedisRateLimiter()
        mock_redis = AsyncMock()
        mock_redis.ttl.return_value = 2400  # Remaining 2400s of cooldown
        limiter.redis = MagicMock(client=mock_redis)

        req = MagicMock(spec=Request)
        req.method = "GET"
        req.headers = {}
        req.client = MagicMock(host="1.2.3.4")

        result = await limiter.check(req)
        assert result.is_allowed is False
        assert result.in_cooldown is True
        assert result.retry_after == 2400
        assert result.remaining == 0
        mock_redis.ttl.assert_called_once_with("ratelimit:cooldown:1.2.3.4")

    asyncio.run(run_test())


def test_rate_limiter_sliding_window_allowed():
    async def run_test():
        limiter = RedisRateLimiter()
        mock_redis = AsyncMock()
        mock_redis.ttl.return_value = -2  # Key does not exist (not in cooldown)

        mock_pipe = AsyncMock()
        mock_pipe.execute.return_value = [0, 1, 5, True]  # 5 requests in current window
        mock_redis.pipeline.return_value = mock_pipe
        limiter.redis = MagicMock(client=mock_redis)

        req = MagicMock(spec=Request)
        req.method = "POST"  # limit = 30
        req.headers = {}
        req.client = MagicMock(host="1.2.3.4")

        result = await limiter.check(req)
        assert result.is_allowed is True
        assert result.limit == 30
        assert result.remaining == 25  # 30 - 5
        assert result.in_cooldown is False
        assert result.retry_after == 0

    asyncio.run(run_test())


def test_rate_limiter_exceed_triggers_cooldown():
    async def run_test():
        limiter = RedisRateLimiter()
        mock_redis = AsyncMock()
        mock_redis.ttl.return_value = -2  # Not in cooldown

        mock_pipe = AsyncMock()
        mock_pipe.execute.return_value = [0, 1, 31, True]  # 31 requests on POST (limit is 30)
        mock_redis.pipeline.return_value = mock_pipe
        limiter.redis = MagicMock(client=mock_redis)

        req = MagicMock(spec=Request)
        req.method = "POST"
        req.headers = {}
        req.client = MagicMock(host="1.2.3.4")

        result = await limiter.check(req)
        assert result.is_allowed is False
        assert result.in_cooldown is True
        assert result.retry_after == 3600  # 1 hour cooldown
        assert result.remaining == 0

        # Verify cooldown was stored in Redis for 3600 seconds
        mock_redis.set.assert_called_once_with("ratelimit:cooldown:1.2.3.4", "1", ex=3600)
        mock_redis.delete.assert_called_once_with("ratelimit:reqs:1.2.3.4:post")

    asyncio.run(run_test())


def test_rate_limit_middleware_allowed():
    async def run_test():
        app = MagicMock()
        middleware = RateLimitMiddleware(app)

        req = MagicMock(spec=Request)
        req.method = "GET"
        req.url.path = "/api/v1/stays"
        req.headers = {}
        req.client = MagicMock(host="1.2.3.4")

        # Mock call_next
        mock_response = Response(content="ok", status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        # Mock rate limiter to return allowed
        allowed_result = RateLimitResult(
            is_allowed=True,
            limit=120,
            remaining=119,
            window_seconds=60,
            reset_seconds=60,
            cooldown_seconds=3600,
            retry_after=0,
            in_cooldown=False,
            method="GET",
            ip="1.2.3.4",
        )
        with patch("app.core.rate_limiter.rate_limiter.check", AsyncMock(return_value=allowed_result)):
            response = await middleware.dispatch(req, call_next)

            assert response.status_code == 200
            assert response.headers["X-RateLimit-Limit"] == "120"
            assert response.headers["X-RateLimit-Remaining"] == "119"
            assert response.headers["X-RateLimit-Reset"] == "60"
            assert response.headers["X-RateLimit-Window"] == "60"
            assert response.headers["X-RateLimit-Method"] == "GET"

    asyncio.run(run_test())


def test_rate_limit_middleware_blocked_429():
    async def run_test():
        import json
        app = MagicMock()
        middleware = RateLimitMiddleware(app)

        req = MagicMock(spec=Request)
        req.method = "DELETE"
        req.url.path = "/api/v1/properties/123"
        req.headers = {}
        req.client = MagicMock(host="5.6.7.8")

        call_next = AsyncMock()

        blocked_result = RateLimitResult(
            is_allowed=False,
            limit=20,
            remaining=0,
            window_seconds=60,
            reset_seconds=3600,
            cooldown_seconds=3600,
            retry_after=3600,
            in_cooldown=True,
            method="DELETE",
            ip="5.6.7.8",
        )
        with patch("app.core.rate_limiter.rate_limiter.check", AsyncMock(return_value=blocked_result)):
            response = await middleware.dispatch(req, call_next)

            assert response.status_code == 429
            assert response.headers["Retry-After"] == "3600"
            assert response.headers["X-RateLimit-Limit"] == "20"
            assert response.headers["X-RateLimit-Remaining"] == "0"
            assert response.headers["X-RateLimit-Cooldown"] == "3600"
            assert response.headers["X-RateLimit-Method"] == "DELETE"

            body = json.loads(response.body.decode())
            assert body["status"] == "error"
            assert body["error_code"] == "RATE_LIMIT_EXCEEDED"
            assert body["retry_after"] == 3600
            assert body["rate_limit"]["method"] == "DELETE"
            assert body["rate_limit"]["limit"] == 20
            assert body["rate_limit"]["cooldown_seconds"] == 3600
            assert body["rate_limit"]["is_cooldown"] is True

            # Ensure downstream route handler was never called
            call_next.assert_not_called()

    asyncio.run(run_test())


def test_rate_limiter_dependency():
    async def run_test():
        dep = RateLimiter(max_requests=5, window_seconds=10, cooldown_seconds=1800)
        req = MagicMock(spec=Request)
        req.method = "POST"
        req.headers = {}
        req.client = MagicMock(host="9.9.9.9")

        blocked_result = RateLimitResult(
            is_allowed=False,
            limit=5,
            remaining=0,
            window_seconds=10,
            reset_seconds=1800,
            cooldown_seconds=1800,
            retry_after=1800,
            in_cooldown=True,
            method="POST",
            ip="9.9.9.9",
        )
        with patch("app.core.rate_limiter.rate_limiter.check", AsyncMock(return_value=blocked_result)):
            with pytest.raises(RateLimitExceededError) as exc_info:
                await dep(req)

            assert exc_info.value.status_code == 429
            assert exc_info.value.retry_after == 1800
            assert exc_info.value.detail["error_code"] == "RATE_LIMIT_EXCEEDED"
            assert exc_info.value.detail["details"]["limit"] == 5
            assert exc_info.value.detail["details"]["cooldown_seconds"] == 1800

    asyncio.run(run_test())

