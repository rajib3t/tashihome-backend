import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import Message

from app.core.config import settings
from app.core.exceptions import (
    IdempotencyConflictError,
    IdempotencyMismatchError,
)
from app.core.redis import redis_client
from app.core.security import TokenManager

logger = logging.getLogger(__name__)

IDEMPOTENCY_HEADER_NAMES: Tuple[str, ...] = (
    "idempotency-key",
    "x-idempotency-key",
)


def extract_idempotency_key(request: Request) -> Optional[str]:
    """Extract and sanitize Idempotency-Key or X-Idempotency-Key from headers."""
    for header in IDEMPOTENCY_HEADER_NAMES:
        val = request.headers.get(header)
        if val and val.strip():
            return val.strip()
    return None


async def extract_user_scope(request: Request) -> str:
    """
    Extract a unique user identifier (user_id or client_ip) to scope idempotency keys.
    Prevents key collisions or access across different users.
    """
    # 1. Check Bearer token
    auth_header = request.headers.get("authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif request.cookies.get("access_token"):
        token = request.cookies.get("access_token")

    if token:
        try:
            token_manager = TokenManager()
            payload = await token_manager.decode_token(token)
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass

    # 2. Fallback to IP address
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
        if ip:
            return f"ip:{ip}"

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return f"ip:{x_real_ip.strip()}"

    if request.client and request.client.host:
        return f"ip:{request.client.host.strip()}"

    return "ip:127.0.0.1"


def compute_request_hash(
    method: str,
    path: str,
    query_string: str,
    body: bytes,
    scope: str,
) -> str:
    """Generate SHA-256 fingerprint of request method, path, query, scope, and body."""
    hasher = hashlib.sha256()
    hasher.update(method.upper().encode("utf-8"))
    hasher.update(b"|")
    hasher.update(path.encode("utf-8"))
    hasher.update(b"|")
    hasher.update(query_string.encode("utf-8"))
    hasher.update(b"|")
    hasher.update(scope.encode("utf-8"))
    hasher.update(b"|")
    hasher.update(body)
    return hasher.hexdigest()


class IdempotencyManager:
    """
    Manages Redis storage, atomic locking, response caching, and replay for idempotency keys.
    """

    def __init__(self):
        self.redis = redis_client

    def _make_key(self, scope: str, idempotency_key: str) -> str:
        prefix = settings.IDEMPOTENCY_KEY_PREFIX
        return f"{prefix}:{scope}:{idempotency_key}"

    async def get_record(self, scope: str, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored idempotency record from Redis."""
        if not settings.IDEMPOTENCY_ENABLED or self.redis.client is None:
            return None

        redis_key = self._make_key(scope, idempotency_key)
        try:
            raw = await self.redis.client.get(redis_key)
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning("Error reading idempotency key from Redis: %s", e)
        return None

    async def acquire_lock(
        self,
        scope: str,
        idempotency_key: str,
        request_hash: str,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Attempt to acquire in-flight lock for idempotency key.
        Returns:
            (is_locked, existing_record)
            - If is_locked is True: Lock acquired, proceed with execution.
            - If is_locked is False: Key already exists (either IN_PROGRESS or COMPLETED).
        """
        if not settings.IDEMPOTENCY_ENABLED or self.redis.client is None:
            # Bypass locking if disabled or Redis is unavailable
            return True, None

        redis_key = self._make_key(scope, idempotency_key)
        lock_data = {
            "status": "IN_PROGRESS",
            "request_hash": request_hash,
            "started_at": time.time(),
        }

        try:
            # Atomic SET if Not eXists with lock expiration TTL
            acquired = await self.redis.client.set(
                redis_key,
                json.dumps(lock_data),
                nx=True,
                ex=settings.IDEMPOTENCY_LOCK_TIMEOUT_SECONDS,
            )
            if acquired:
                return True, None

            # Already exists: fetch the existing record
            raw = await self.redis.client.get(redis_key)
            if raw:
                return False, json.loads(raw)
            return True, None

        except Exception as e:
            logger.warning("Error acquiring idempotency lock in Redis: %s", e)
            # Fail open on Redis errors
            return True, None

    async def save_response(
        self,
        scope: str,
        idempotency_key: str,
        request_hash: str,
        status_code: int,
        headers: Dict[str, str],
        body: str,
    ) -> bool:
        """Persist completed response to Redis with configured expiration."""
        if not settings.IDEMPOTENCY_ENABLED or self.redis.client is None:
            return False

        redis_key = self._make_key(scope, idempotency_key)

        # Filter out transport-specific headers
        filtered_headers = {}
        excluded_headers = {
            "content-length",
            "server",
            "date",
            "transfer-encoding",
            "connection",
            "set-cookie",
        }
        for k, v in headers.items():
            if k.lower() not in excluded_headers:
                filtered_headers[k] = v

        record = {
            "status": "COMPLETED",
            "request_hash": request_hash,
            "status_code": status_code,
            "headers": filtered_headers,
            "body": body,
            "completed_at": time.time(),
        }

        try:
            await self.redis.client.set(
                redis_key,
                json.dumps(record),
                ex=settings.IDEMPOTENCY_EXPIRE_SECONDS,
            )
            return True
        except Exception as e:
            logger.warning("Error saving idempotency response to Redis: %s", e)
            return False

    async def release_lock(self, scope: str, idempotency_key: str) -> None:
        """Release lock / remove key from Redis upon error so client can retry."""
        if not settings.IDEMPOTENCY_ENABLED or self.redis.client is None:
            return

        redis_key = self._make_key(scope, idempotency_key)
        try:
            await self.redis.client.delete(redis_key)
        except Exception as e:
            logger.warning("Error releasing idempotency lock in Redis: %s", e)


idempotency_manager = IdempotencyManager()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts requests containing Idempotency-Key headers.
    Features:
    1. Replays completed responses transparently (Idempotent-Replay: true).
    2. Blocks concurrent duplicate requests with 409 Conflict.
    3. Rejects modified payloads with the same key with 422 Unprocessable Entity.
    4. Automatically releases locks on 5xx errors or server exceptions to enable retries.
    """

    IDEMPOTENT_METHODS: Set[str] = {"POST", "PATCH", "PUT", "DELETE"}

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
        # Only process state-changing methods
        if request.method not in self.IDEMPOTENT_METHODS:
            return await call_next(request)

        # Skip excluded endpoints
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        idempotency_key = extract_idempotency_key(request)
        # If no key was provided in headers, let request pass through normally
        if not idempotency_key:
            return await call_next(request)

        # Read the entire request body bytes for fingerprinting
        body_bytes = await request.body()

        # Re-populate the request receive channel so downstream handlers can read body
        async def receive() -> Message:
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request._receive = receive

        scope = await extract_user_scope(request)
        request_hash = compute_request_hash(
            method=request.method,
            path=request.url.path,
            query_string=str(request.url.query),
            body=body_bytes,
            scope=scope,
        )

        # Try to acquire lock or check existing record
        acquired, existing_record = await idempotency_manager.acquire_lock(
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )

        if not acquired and existing_record:
            stored_hash = existing_record.get("request_hash")
            status = existing_record.get("status")

            # 1. Payload Mismatch: Same key used with different payload/route
            if stored_hash and stored_hash != request_hash:
                logger.warning(
                    "Idempotency payload mismatch for key %s (scope: %s, path: %s)",
                    idempotency_key,
                    scope,
                    request.url.path,
                )
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": "error",
                        "message": "This idempotency key was previously used with a different request payload or target URL.",
                        "error_code": "IDEMPOTENCY_PAYLOAD_MISMATCH",
                    },
                    headers={"X-Idempotency-Key": idempotency_key},
                )

            # 2. In Progress: Concurrent request
            if status == "IN_PROGRESS":
                logger.info(
                    "Concurrent in-progress request detected for key %s (scope: %s)",
                    idempotency_key,
                    scope,
                )
                return JSONResponse(
                    status_code=409,
                    content={
                        "status": "error",
                        "message": "A request with this idempotency key is currently being processed. Please wait.",
                        "error_code": "IDEMPOTENCY_CONFLICT",
                    },
                    headers={"X-Idempotency-Key": idempotency_key},
                )

            # 3. Completed: Replay cached response
            if status == "COMPLETED":
                logger.info(
                    "Replaying cached response for idempotency key %s (scope: %s)",
                    idempotency_key,
                    scope,
                )
                cached_status = existing_record.get("status_code", 200)
                cached_headers = dict(existing_record.get("headers", {}))
                cached_body = existing_record.get("body", "")

                cached_headers["Idempotent-Replay"] = "true"
                cached_headers["X-Idempotency-Key"] = idempotency_key

                media_type = cached_headers.get("content-type", "application/json")

                return Response(
                    content=cached_body,
                    status_code=cached_status,
                    headers=cached_headers,
                    media_type=media_type,
                )

        # Proceed with executing the downstream route handler
        try:
            response = await call_next(request)

            # Read response body stream
            response_body_chunks = [chunk async for chunk in response.body_iterator]
            response_bytes = b"".join(response_body_chunks)
            response_text = response_bytes.decode("utf-8", errors="replace")

            # Only cache responses with status code < 500 (2xx, 3xx, 4xx)
            if response.status_code < 500:
                await idempotency_manager.save_response(
                    scope=scope,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response_text,
                )
            else:
                # 5xx Server Error: release the lock so client can retry
                await idempotency_manager.release_lock(scope, idempotency_key)

            # Build and return the response with Idempotency header
            headers = dict(response.headers)
            headers["X-Idempotency-Key"] = idempotency_key

            return Response(
                content=response_bytes,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )

        except Exception as exc:
            # Release lock on unexpected server exceptions so client can retry
            await idempotency_manager.release_lock(scope, idempotency_key)
            raise exc

