import logging
import urllib.parse
import uuid
from typing import Any, Optional

import socketio
from sqlalchemy import select

from app.core.config import settings
from app.core.database import db
from app.core.security import TokenManager
from app.models.token_model import TokenType
from app.models.user_model import User, UserRole, UserStatus

logger = logging.getLogger(__name__)

# Determine allowed origins
cors_origins = settings.cors_allowed_origins
if not cors_origins and getattr(settings, "DEBUG", False):
    cors_origins = "*"
elif not cors_origins:
    cors_origins = "*"

# Multi-worker Redis Manager for production clustering
client_manager = None
if getattr(settings, "SOCKETIO_REDIS_ENABLED", False) and settings.REDIS_HOST:
    try:
        auth_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
        redis_url = f"redis://{auth_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB or 0}"
        client_manager = socketio.AsyncRedisManager(redis_url)
        logger.info("Socket.IO initialized with AsyncRedisManager for multi-worker support")
    except Exception as e:
        logger.warning(f"Could not initialize Socket.IO Redis manager: {e}")

# Initialize Socket.IO AsyncServer
# Note: Using async_mode="asgi"
sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=client_manager,
    cors_allowed_origins=cors_origins,
    ping_timeout=30,
    ping_interval=20,
)


def _extract_token_from_environ(environ: dict, auth: Optional[dict] = None) -> Optional[str]:
    """Extract JWT token from socket handshake auth dict, query string, auth header, or cookie."""
    # 1. From auth payload (recommended by socket.io v4 client: io(url, { auth: { token: '...' } }))
    if auth and isinstance(auth, dict):
        token = auth.get("token") or auth.get("access_token")
        if token:
            return token.strip()

    # 2. From query parameters (e.g. ws://...?token=...)
    query_string = environ.get("QUERY_STRING", "")
    if query_string:
        params = urllib.parse.parse_qs(query_string)
        token_param = params.get("token") or params.get("access_token")
        if token_param and token_param[0]:
            return token_param[0].strip()

    # 3. From HTTP Authorization Header
    auth_header = environ.get("HTTP_AUTHORIZATION", "")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # 4. From Cookie header
    cookie_str = environ.get("HTTP_COOKIE", "")
    if cookie_str:
        for chunk in cookie_str.split(";"):
            chunk = chunk.strip()
            if "=" in chunk:
                key, val = chunk.split("=", 1)
                if key.strip() == TokenType.ACCESS.value:
                    return val.strip()

    return None


@sio.event
async def connect(sid: str, environ: dict, auth: Optional[dict] = None):
    """Handshake authentication for incoming socket connections."""
    token = _extract_token_from_environ(environ, auth)
    if not token:
        logger.warning("Socket connection refused [%s]: no auth token provided", sid)
        raise socketio.exceptions.ConnectionRefusedError("authentication_required")

    try:
        token_manager = TokenManager()
        payload = await token_manager.decode_token(token)
    except Exception as exc:
        logger.warning("Socket connection refused [%s]: invalid/expired token (%s)", sid, exc)
        raise socketio.exceptions.ConnectionRefusedError("invalid_token")

    if payload.get("type") != TokenType.ACCESS.value:
        logger.warning("Socket connection refused [%s]: token type is not access token", sid)
        raise socketio.exceptions.ConnectionRefusedError("wrong_token_type")

    sub = payload.get("sub")
    if not sub:
        logger.warning("Socket connection refused [%s]: missing sub claim in token", sid)
        raise socketio.exceptions.ConnectionRefusedError("missing_sub")

    try:
        user_uuid = uuid.UUID(str(sub))
    except (ValueError, AttributeError):
        logger.warning("Socket connection refused [%s]: invalid user UUID in sub", sid)
        raise socketio.exceptions.ConnectionRefusedError("invalid_user_uuid")

    # Validate user exists and is active in database
    if db.async_session is None:
        db.connect()
    async with db.async_session() as session:
        result = await session.execute(select(User).where(User.public_id == user_uuid))
        user = result.scalar_one_or_none()

    if not user or user.status != UserStatus.ACTIVE:
        logger.warning("Socket connection refused [%s]: user not found or inactive (%s)", sid, sub)
        raise socketio.exceptions.ConnectionRefusedError("user_inactive")

    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)

    # Save authenticated session details
    await sio.save_session(sid, {
        "user_id": user.id,
        "public_id": str(user.public_id),
        "role": user_role_str,
        "email": user.email,
        "full_name": user.full_name,
    })

    # Join user personal room: 'user:{user_id}'
    user_room = f"user:{user.id}"
    await sio.enter_room(sid, user_room)

    # Join role room: 'role:{role}' (e.g. 'role:admin', 'role:vendor', 'role:user')
    role_room = f"role:{user_role_str}"
    await sio.enter_room(sid, role_room)

    logger.info(
        "Socket connected [%s]: user_id=%s, role=%s, rooms=[%s, %s]",
        sid,
        user.id,
        user_role_str,
        user_room,
        role_room,
    )
    return True


@sio.event
async def disconnect(sid: str):
    try:
        session = await sio.get_session(sid)
        user_id = session.get("user_id") if session else None
        logger.info("Socket disconnected [%s]: user_id=%s", sid, user_id)
    except Exception:
        logger.info("Socket disconnected [%s]", sid)


@sio.event
async def ping(sid: str, data: Any = None):
    """Heartbeat response."""
    return {"pong": True, "sid": sid}


# Real-time Broadcast Helpers
async def emit_to_user(user_id: int, event: str, data: dict[str, Any]) -> None:
    """Send an event to all socket connections belonging to a specific user."""
    room = f"user:{user_id}"
    try:
        await sio.emit(event, data, room=room)
        logger.debug("Emitted socket event '%s' to room '%s'", event, room)
    except Exception as exc:
        logger.error("Failed to emit socket event '%s' to room '%s': %s", event, room, exc)


async def emit_to_role(role: str, event: str, data: dict[str, Any]) -> None:
    """Send an event to all socket connections belonging to a specific role (e.g. 'admin', 'vendor')."""
    room = f"role:{role}"
    try:
        await sio.emit(event, data, room=room)
        logger.debug("Emitted socket event '%s' to role room '%s'", event, room)
    except Exception as exc:
        logger.error("Failed to emit socket event '%s' to role room '%s': %s", event, room, exc)


async def emit_to_admins(event: str, data: dict[str, Any]) -> None:
    """Send an event to all online administrators."""
    await emit_to_role(UserRole.ADMIN.value, event, data)


async def emit_notification(user_id: int, role: str, payload: dict[str, Any]) -> None:
    """Send real-time notification to user personal channel and role channel."""
    await emit_to_user(user_id, "notification", payload)
