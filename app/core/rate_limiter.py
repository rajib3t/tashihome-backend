import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request headers or remote connection.
    Supports reverse proxies via X-Forwarded-For and X-Real-IP headers.
    """
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # X-Forwarded-For can be a comma-separated list; the first IP is the original client
        client_ip = x_forwarded_for.split(",")[0].strip()
        if client_ip:
            return client_ip

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        client_ip = x_real_ip.strip()
        if client_ip:
            return client_ip

    if request.client and request.client.host:
        return request.client.host.strip()

    return "127.0.0.1"


@dataclass
class RateLimitResult:
    is_allowed: bool
    limit: int
    remaining: int
    window_seconds: int
    reset_seconds: int
    cooldown_seconds: int
    retry_after: int
    in_cooldown: bool
    method: str
    ip: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "limit": self.limit,
            "remaining": self.remaining,
            "window_seconds": self.window_seconds,
            "cooldown_seconds": self.cooldown_seconds,
            "retry_after": self.retry_after,
            "is_cooldown": self.in_cooldown,
        }


class RedisRateLimiter:
    """
    Redis-based rate limiter using sliding window log and automatic IP cooldown.
    Supports method-specific limits (GET, POST, PUT, PATCH, DELETE) and setting-driven intervals.
    """

    def __init__(self):
        self.redis = redis_client

    async def check(
        self,
        request: Request,
        custom_limit: Optional[int] = None,
        custom_window: Optional[int] = None,
        custom_cooldown: Optional[int] = None,
    ) -> RateLimitResult:
        method = (request.method or "GET").upper()
        client_ip = get_client_ip(request)

        # Retrieve settings for this HTTP method
        default_limit, default_window = settings.get_rate_limit_for_method(method)
        limit = custom_limit if custom_limit is not None else default_limit
        window_seconds = custom_window if custom_window is not None else default_window
        cooldown_seconds = (
            custom_cooldown if custom_cooldown is not None else settings.RATE_LIMIT_COOLDOWN_SECONDS
        )
        prefix = settings.RATE_LIMIT_KEY_PREFIX

        # If rate limiting is disabled or Redis client is unavailable, allow request (fail-open)
        if not settings.RATE_LIMIT_ENABLED:
            return RateLimitResult(
                is_allowed=True,
                limit=limit,
                remaining=limit,
                window_seconds=window_seconds,
                reset_seconds=window_seconds,
                cooldown_seconds=cooldown_seconds,
                retry_after=0,
                in_cooldown=False,
                method=method,
                ip=client_ip,
            )

        if self.redis.client is None:
            logger.debug("Redis client not connected; bypassing rate limiting")
            return RateLimitResult(
                is_allowed=True,
                limit=limit,
                remaining=limit,
                window_seconds=window_seconds,
                reset_seconds=window_seconds,
                cooldown_seconds=cooldown_seconds,
                retry_after=0,
                in_cooldown=False,
                method=method,
                ip=client_ip,
            )

        cooldown_key = f"{prefix}:cooldown:{client_ip}"
        reqs_key = f"{prefix}:reqs:{client_ip}:{method.lower()}"

        try:
            # 1. Check if the IP is currently in cooldown (1-hour temporary block)
            cooldown_ttl = await self.redis.client.ttl(cooldown_key)
            if cooldown_ttl > 0:
                logger.warning(
                    "Rate limit cooldown active for IP %s on %s (TTL: %s seconds)",
                    client_ip,
                    method,
                    cooldown_ttl,
                )
                return RateLimitResult(
                    is_allowed=False,
                    limit=limit,
                    remaining=0,
                    window_seconds=window_seconds,
                    reset_seconds=cooldown_ttl,
                    cooldown_seconds=cooldown_seconds,
                    retry_after=cooldown_ttl,
                    in_cooldown=True,
                    method=method,
                    ip=client_ip,
                )

            # 2. Sliding window rate limit check using Redis Sorted Set (ZSET)
            now = time.time()
            window_start = now - window_seconds
            unique_member = f"{now}:{uuid.uuid4().hex[:6]}"

            pipeline = self.redis.client.pipeline()
            # Remove records older than the window
            pipeline.zremrangebyscore(reqs_key, 0, window_start)
            # Add the current request
            pipeline.zadd(reqs_key, {unique_member: now})
            # Count total requests in window
            pipeline.zcard(reqs_key)
            # Set TTL on the request set
            pipeline.expire(reqs_key, window_seconds + 10)

            results = await pipeline.execute()
            current_count = int(results[2])

            if current_count > limit:
                # Limit exceeded! Place IP on cooldown for 1 hour (setting-driven)
                logger.warning(
                    "IP %s exceeded %s limit (%d/%d in %ds). Triggering %ds cooldown.",
                    client_ip,
                    method,
                    current_count,
                    limit,
                    window_seconds,
                    cooldown_seconds,
                )
                await self.redis.client.set(cooldown_key, "1", ex=cooldown_seconds)
                # Cleanup the request window key
                await self.redis.client.delete(reqs_key)

                return RateLimitResult(
                    is_allowed=False,
                    limit=limit,
                    remaining=0,
                    window_seconds=window_seconds,
                    reset_seconds=cooldown_seconds,
                    cooldown_seconds=cooldown_seconds,
                    retry_after=cooldown_seconds,
                    in_cooldown=True,
                    method=method,
                    ip=client_ip,
                )

            remaining = max(0, limit - current_count)
            return RateLimitResult(
                is_allowed=True,
                limit=limit,
                remaining=remaining,
                window_seconds=window_seconds,
                reset_seconds=window_seconds,
                cooldown_seconds=cooldown_seconds,
                retry_after=0,
                in_cooldown=False,
                method=method,
                ip=client_ip,
            )

        except Exception as exc:
            logger.warning("Error checking rate limit in Redis for IP %s: %s", client_ip, exc)
            # Graceful fail-open on unexpected Redis errors
            return RateLimitResult(
                is_allowed=True,
                limit=limit,
                remaining=limit,
                window_seconds=window_seconds,
                reset_seconds=window_seconds,
                cooldown_seconds=cooldown_seconds,
                retry_after=0,
                in_cooldown=False,
                method=method,
                ip=client_ip,
            )


rate_limiter = RedisRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware applying setting-driven rate limiting with IP cooldown across HTTP endpoints.
    Attaches rate limit information to response headers and returns detailed JSON payload on 429.
    """

    EXCLUDED_PATHS: Set[str] = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }

    def __init__(self, app, excluded_paths: Optional[Set[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or self.EXCLUDED_PATHS

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip OPTIONS preflight requests to avoid breaking CORS
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip excluded endpoints (e.g. root health check and docs)
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Check rate limit
        result = await rate_limiter.check(request)

        if not result.is_allowed:
            cooldown_hours = max(1, round(result.cooldown_seconds / 3600))
            message = (
                f"Too many requests for {result.method}. Your IP has been temporarily blocked for "
                f"{cooldown_hours} hour{'s' if cooldown_hours > 1 else ''}. Please try again later."
            )

            headers = {
                "Retry-After": str(result.retry_after),
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(result.retry_after),
                "X-RateLimit-Window": str(result.window_seconds),
                "X-RateLimit-Method": result.method,
                "X-RateLimit-Cooldown": str(result.cooldown_seconds),
            }

            content = {
                "status": "error",
                "message": message,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": result.retry_after,
                "rate_limit": result.to_dict(),
            }

            return JSONResponse(
                status_code=429,
                content=content,
                headers=headers,
            )

        response = await call_next(request)

        # Attach rate limit details to response headers
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_seconds)
        response.headers["X-RateLimit-Window"] = str(result.window_seconds)
        response.headers["X-RateLimit-Method"] = result.method

        return response


class RateLimiter:
    """
    FastAPI dependency for route-specific custom rate limits.
    """

    def __init__(
        self,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
        cooldown_seconds: Optional[int] = None,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cooldown_seconds = cooldown_seconds

    async def __call__(self, request: Request):
        result = await rate_limiter.check(
            request=request,
            custom_limit=self.max_requests,
            custom_window=self.window_seconds,
            custom_cooldown=self.cooldown_seconds,
        )

        if not result.is_allowed:
            raise RateLimitExceededError(
                message=f"Rate limit exceeded for {result.method}. IP on cooldown for {result.retry_after}s.",
                retry_after=result.retry_after,
                details=result.to_dict(),
            )
        return result

