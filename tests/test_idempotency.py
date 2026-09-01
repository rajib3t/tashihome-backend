import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import Settings, settings
from app.core.exceptions import (
    IdempotencyConflictError,
    IdempotencyKeyRequiredError,
    IdempotencyMismatchError,
)
from app.core.idempotency import (
    IdempotencyManager,
    IdempotencyMiddleware,
    compute_request_hash,
    extract_idempotency_key,
    extract_user_scope,
)
from app.deps.idempotency import require_idempotency_key


def test_idempotency_settings_defaults():
    s = Settings(
        APP_NAME="Test",
        DATABASE_URL="postgresql://test:test@localhost:5432/test",
        JWT_SECRET="secret",
    )
    assert s.IDEMPOTENCY_ENABLED is True
    assert s.IDEMPOTENCY_EXPIRE_SECONDS == 86400
    assert s.IDEMPOTENCY_LOCK_TIMEOUT_SECONDS == 30
    assert s.IDEMPOTENCY_KEY_PREFIX == "idempotency"


def test_extract_idempotency_key():
    req1 = MagicMock(spec=Request)
    req1.headers = {"idempotency-key": "test-uuid-1234"}
    assert extract_idempotency_key(req1) == "test-uuid-1234"

    req2 = MagicMock(spec=Request)
    req2.headers = {"x-idempotency-key": "  test-uuid-5678  "}
    assert extract_idempotency_key(req2) == "test-uuid-5678"

    req3 = MagicMock(spec=Request)
    req3.headers = {}
    assert extract_idempotency_key(req3) is None

    req4 = MagicMock(spec=Request)
    req4.headers = {"idempotency-key": "   "}
    assert extract_idempotency_key(req4) is None


def test_compute_request_hash():
    h1 = compute_request_hash("POST", "/api/v1/user/bookings/", "", b'{"property_id": 1}', "user:42")
    h2 = compute_request_hash("POST", "/api/v1/user/bookings/", "", b'{"property_id": 1}', "user:42")
    h3 = compute_request_hash("POST", "/api/v1/user/bookings/", "", b'{"property_id": 2}', "user:42")
    h4 = compute_request_hash("POST", "/api/v1/user/bookings/", "", b'{"property_id": 1}', "user:99")

    assert h1 == h2
    assert h1 != h3
    assert h1 != h4


@pytest.mark.asyncio
async def test_extract_user_scope_ip_and_auth():
    # 1. Fallback to client host
    req1 = MagicMock(spec=Request)
    req1.headers = {}
    req1.cookies = {}
    req1.client = MagicMock(host="192.168.1.100")
    assert await extract_user_scope(req1) == "ip:192.168.1.100"

    # 2. X-Forwarded-For
    req2 = MagicMock(spec=Request)
    req2.headers = {"x-forwarded-for": "203.0.113.1, 10.0.0.1"}
    req2.cookies = {}
    req2.client = None
    assert await extract_user_scope(req2) == "ip:203.0.113.1"

    # 3. Valid JWT Token
    req3 = MagicMock(spec=Request)
    req3.headers = {"authorization": "Bearer valid.jwt.token"}
    req3.cookies = {}
    with patch("app.core.idempotency.TokenManager.decode_token", new_callable=AsyncMock) as mock_decode:
        mock_decode.return_value = {"sub": 77, "role": "user"}
        assert await extract_user_scope(req3) == "user:77"


@pytest.mark.asyncio
async def test_idempotency_manager_lifecycle():
    manager = IdempotencyManager()
    mock_redis = AsyncMock()
    manager.redis = MagicMock(client=mock_redis)

    scope = "user:123"
    key = "test-key-abc"
    req_hash = "fake-sha256"

    # 1. Acquire new lock (SET NX returns True)
    mock_redis.set.return_value = True
    acquired, existing = await manager.acquire_lock(scope, key, req_hash)
    assert acquired is True
    assert existing is None
    mock_redis.set.assert_called_once_with(
        "idempotency:user:123:test-key-abc",
        json.dumps({"status": "IN_PROGRESS", "request_hash": req_hash, "started_at": pytest.approx(0, abs=1e10)}),
        nx=True,
        ex=settings.IDEMPOTENCY_LOCK_TIMEOUT_SECONDS,
    )

    # 2. Save completed response
    mock_redis.set.reset_mock()
    mock_redis.set.return_value = True
    saved = await manager.save_response(
        scope, key, req_hash, 201, {"content-type": "application/json"}, '{"id": 1}'
    )
    assert saved is True
    assert mock_redis.set.call_count == 1

    # 3. Release lock
    mock_redis.delete.return_value = 1
    await manager.release_lock(scope, key)
    mock_redis.delete.assert_called_once_with("idempotency:user:123:test-key-abc")


@pytest.mark.asyncio
async def test_require_idempotency_key_dependency():
    # Missing header -> 400
    req_missing = MagicMock(spec=Request)
    req_missing.headers = {}
    with pytest.raises(IdempotencyKeyRequiredError):
        await require_idempotency_key(req_missing)

    # Too short -> 400
    req_short = MagicMock(spec=Request)
    req_short.headers = {"idempotency-key": "short"}
    with pytest.raises(IdempotencyKeyRequiredError):
        await require_idempotency_key(req_short)

    # Valid key -> returns key string
    req_valid = MagicMock(spec=Request)
    req_valid.headers = {"idempotency-key": "8b9cf2a7-5420-4a8e-8a14-4eb95f190ddb"}
    key = await require_idempotency_key(req_valid)
    assert key == "8b9cf2a7-5420-4a8e-8a14-4eb95f190ddb"


@pytest.mark.asyncio
async def test_middleware_full_flow():
    app_mock = MagicMock()
    middleware = IdempotencyMiddleware(app_mock)

    # Mock IdempotencyManager
    with patch("app.core.idempotency.idempotency_manager") as mock_mgr, \
         patch("app.core.idempotency.extract_user_scope", new_callable=AsyncMock) as mock_scope:
        
        mock_scope.return_value = "user:42"

        # Case 1: First request (executes handler & caches)
        mock_mgr.acquire_lock = AsyncMock(return_value=(True, None))
        mock_mgr.save_response = AsyncMock(return_value=True)

        async def handler(req):
            return JSONResponse(status_code=201, content={"status": "success", "booking_id": 99})

        req1 = Request({
            "type": "http",
            "method": "POST",
            "path": "/api/v1/user/bookings/",
            "headers": [(b"idempotency-key", b"key-12345678"), (b"content-type", b"application/json")],
            "query_string": b"",
        })
        req1._body = b'{"room_type_id": 5}'

        res1 = await middleware.dispatch(req1, handler)
        assert res1.status_code == 201
        assert res1.headers.get("X-Idempotency-Key") == "key-12345678"
        assert mock_mgr.save_response.called

        # Case 2: Duplicate completed request (replays cached response)
        req_hash = compute_request_hash("POST", "/api/v1/user/bookings/", "", b'{"room_type_id": 5}', "user:42")
        mock_mgr.acquire_lock = AsyncMock(return_value=(False, {
            "status": "COMPLETED",
            "request_hash": req_hash,
            "status_code": 201,
            "headers": {"content-type": "application/json"},
            "body": json.dumps({"status": "success", "booking_id": 99}),
        }))

        req2 = Request({
            "type": "http",
            "method": "POST",
            "path": "/api/v1/user/bookings/",
            "headers": [(b"idempotency-key", b"key-12345678"), (b"content-type", b"application/json")],
            "query_string": b"",
        })
        req2._body = b'{"room_type_id": 5}'

        res2 = await middleware.dispatch(req2, handler)
        assert res2.status_code == 201
        assert res2.headers.get("Idempotent-Replay") == "true"
        assert res2.headers.get("X-Idempotency-Key") == "key-12345678"

        # Case 3: Concurrent in-progress request (409 Conflict)
        mock_mgr.acquire_lock = AsyncMock(return_value=(False, {
            "status": "IN_PROGRESS",
            "request_hash": req_hash,
        }))

        req3 = Request({
            "type": "http",
            "method": "POST",
            "path": "/api/v1/user/bookings/",
            "headers": [(b"idempotency-key", b"key-12345678")],
            "query_string": b"",
        })
        req3._body = b'{"room_type_id": 5}'

        res3 = await middleware.dispatch(req3, handler)
        assert res3.status_code == 409
        body3 = json.loads(res3.body)
        assert body3["error_code"] == "IDEMPOTENCY_CONFLICT"

        # Case 4: Payload mismatch (422 Unprocessable Entity)
        mock_mgr.acquire_lock = AsyncMock(return_value=(False, {
            "status": "COMPLETED",
            "request_hash": "different_previous_hash",
        }))

        req4 = Request({
            "type": "http",
            "method": "POST",
            "path": "/api/v1/user/bookings/",
            "headers": [(b"idempotency-key", b"key-12345678")],
            "query_string": b"",
        })
        req4._body = b'{"room_type_id": 5}'

        res4 = await middleware.dispatch(req4, handler)
        assert res4.status_code == 422
        body4 = json.loads(res4.body)
        assert body4["error_code"] == "IDEMPOTENCY_PAYLOAD_MISMATCH"

