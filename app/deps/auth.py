from app.application.use_case.auth.active_account_use_case import ActiveAccountUseCase
from app.core.events import EventBus
from dataclasses import dataclass
import logging
import uuid
from typing import TYPE_CHECKING
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.use_case.auth.login_use_case import LoginUseCase
from app.application.use_case.auth.refresh_token_use_case import RefreshTokenUseCase
from app.core.csrf import verify_csrf
from app.core.exceptions import AppException, TokenExpiredError, TokenInvalidError
from app.core.security import TokenManager
from app.deps.service import get_ip_service, get_login_log_service, get_token_service, get_user_service
from app.models.token_model import TokenType
from app.models.user_model import UserRole
from app.services.ip_service import IpService
from app.services.login_log_service import LoginLogService
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.application.use_case.auth.register_use_case import RegisterUseCase
from app.deps.event_bus import get_event_bus
if TYPE_CHECKING:
    from app.application.use_case.auth.logout_use_case import LogoutUseCase

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


async def get_login_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    login_log_service: LoginLogService = Depends(get_login_log_service),
    ip_service: IpService = Depends(get_ip_service),
) -> LoginUseCase:
    return LoginUseCase(user_service, token_service, login_log_service, ip_service)



async def get_refresh_token_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(user_service, token_service)



@dataclass
class CurrentUser:
    id: int
    role: str


async def extract_token(
    credentials: HTTPAuthorizationCredentials | None,
    request: Request,
) -> str | None:
    if credentials:
        return credentials.credentials

    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    # Fallback to httponly cookie — required since access tokens are set as cookies
    return request.cookies.get(TokenType.ACCESS.value)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_service: UserService = Depends(get_user_service),
) -> CurrentUser:
    """Dependency that returns the current user from an access token.

    Accepts `Authorization: Bearer <token>` or cookie `access_token`.

    Raises:
        AppException(401): If token is missing, invalid, expired, lacks required claims,
                            or does not resolve to an existing user.
    """
    token = await extract_token(credentials, request)

    if not token:
        logger.warning("Auth failure [%s]: no token provided", request.url.path)
        raise AppException(401, "Authorization token missing", error_code="TOKEN_MISSING")

    try:
        token_manager = TokenManager()
        payload = await token_manager.decode_token(token)
        logger.info("Auth success [%s]: user_id=%s, role=%s", request.url.path, payload.get("sub"), payload.get("role"))
    except TokenExpiredError:
        logger.warning("Auth failure [%s]: token expired", request.url.path)
        raise AppException(401, "Token has expired", error_code="TOKEN_EXPIRED")
    except TokenInvalidError as e:
        logger.warning("Auth failure [%s]: invalid token — %s", request.url.path, str(e))
        raise AppException(401, "Invalid token", error_code="TOKEN_INVALID")

    token_type = payload.get("type")
    if token_type != TokenType.ACCESS.value:
        logger.warning("Auth failure [%s]: wrong token type '%s'", request.url.path, token_type)
        raise AppException(401, f"Expected access token, got '{token_type}'", error_code="TOKEN_WRONG_TYPE")

    sub = payload.get("sub")
    role = payload.get("role")
    role = role.value if hasattr(role, "value") else str(role)

    if not sub:
        logger.warning("Auth failure [%s]: missing 'sub' claim", request.url.path)
        raise AppException(401, "Token missing subject claim", error_code="TOKEN_MISSING_SUB")

    if not role:
        logger.warning("Auth failure [%s]: missing 'role' claim", request.url.path)
        raise AppException(401, "Token missing role claim", error_code="TOKEN_MISSING_ROLE")

    public_id = str(sub)

    try:
        uuid.UUID(public_id)
        is_valid_uuid = True
    except (ValueError, AttributeError):
        is_valid_uuid = False

    user = await user_service.get_user_by_public_id(public_id) if is_valid_uuid else None

    if not is_valid_uuid or user is None:
        logger.warning("Auth failure [%s]: user not found for sub=%s", request.url.path, public_id)
        raise AppException(401, "User not found", error_code="TOKEN_INVALID_USER")

    return CurrentUser(id=user.id, role=role)


async def require_role(current_user: CurrentUser, required_roles: list[UserRole]) -> CurrentUser:
    """Checks if the current user has one of the required roles.

    Note: this is a plain helper, not a FastAPI dependency itself — call it
    from the require_* dependencies below, which DO carry the Depends(get_current_user).
    """
    user_role = current_user.role
    if isinstance(user_role, UserRole):
        user_role = user_role.value

    allowed_roles = [r.value if isinstance(r, UserRole) else r for r in required_roles]

    if user_role not in allowed_roles:
        logger.warning(
            "Access denied: user id=%s with role '%s' tried to access endpoint requiring roles: %s",
            current_user.id, user_role, allowed_roles,
        )
        raise AppException(403, f"Access denied. Required role: one of {allowed_roles}", error_code="INSUFFICIENT_PERMISSIONS")

    return current_user


async def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return await require_role(current_user, [UserRole.ADMIN])


async def require_vendor(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return await require_role(current_user, [UserRole.VENDOR])


async def require_admin_or_vendor(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return await require_role(current_user, [UserRole.ADMIN, UserRole.VENDOR])


async def require_user(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return await require_role(current_user, [UserRole.USER])


async def get_logout_use_case(
    token_service: TokenService = Depends(get_token_service),
    verify_csrf = Depends(verify_csrf),
    current_user: "CurrentUser" = Depends(get_current_user),
) -> LogoutUseCase:
    from app.application.use_case.auth.logout_use_case import LogoutUseCase

    return LogoutUseCase(token_service, verify_csrf, current_user)

async def get_register_use_case(
    user_service: UserService = Depends(get_user_service),
    event_bus: EventBus = Depends(get_event_bus),
    verify_csrf = Depends(verify_csrf),
) -> RegisterUseCase:
    

    return RegisterUseCase(user_service, event_bus, verify_csrf)

async def get_active_account_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    verify_csrf = Depends(verify_csrf),    
) -> ActiveAccountUseCase:
    return ActiveAccountUseCase(user_service, token_service, verify_csrf)