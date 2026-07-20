from dataclasses import dataclass
import logging
import uuid
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.use_case.auth.login_use_case import LoginUseCase
from app.application.use_case.auth.refresh_token_use_case import RefreshTokenUseCase
from app.core.exceptions import AppException, TokenExpiredError, TokenInvalidError
from app.core.security import TokenManager
from app.deps.service import get_ip_service, get_login_log_service, get_token_service, get_user_service
from app.models.token_model import TokenType
from app.models.user_model import UserRole
from app.services.ip_service import IpService
from app.services.login_log_service import LoginLogService
from app.services.token_service import TokenService
from app.services.user_service import UserService

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)
# Dependency injection function to provide an instance of LoginUseCase with the required UserService, TokenService, and LoginLogService dependencies.
async def get_login_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    login_log_service: LoginLogService = Depends(get_login_log_service),
    ip_service: IpService = Depends(get_ip_service)  # Injecting IpService dependency
) -> LoginUseCase:
    # Return an instance of LoginUseCase, initialized with the provided UserService and TokenService.
    return LoginUseCase(user_service, token_service, login_log_service, ip_service)

async def get_refresh_token_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service)
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(user_service, token_service)



@dataclass
class CurrentUser:
    id: int
    role: str  # was: role


async def extract_token(
    credentials: HTTPAuthorizationCredentials | None,
    request: Request,
) -> str | None:
    if credentials:
        return credentials.credentials

    auth_header = request.headers.get("authorization") 
    # Extract the token from the Authorization header
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    return None

async def get_current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
        user_service: UserService = Depends(get_user_service),
        ) -> CurrentUser:

    """Dependency that returns the current user from an access token.

    Accepts `Authorization: Bearer <token>` or cookie `access_token`.

    Raises:
        AppException(401): If token is missing, invalid, expired, or lacks required claims.
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
    logger.info("Token type: %s", token_type)
    if token_type != TokenType.ACCESS.value:
        logger.warning(
            "Auth failure [%s]: wrong token type '%s'", request.url.path, token_type
        )
        raise AppException(
            401,
            f"Expected access token, got '{token_type}'",
            error_code="TOKEN_WRONG_TYPE",
        )
    
    sub = payload.get("sub")
    role =  payload.get("role")
    if hasattr(role, "value"):
        role = role.value
    else:
        role = str(role)

    if not sub:
        logger.warning("Auth failure [%s]: missing 'sub' claim", request.url.path)
        raise AppException(401, "Token missing subject claim", error_code="TOKEN_MISSING_SUB")

    if not role:
        logger.warning("Auth failure [%s]: missing 'user_type'/'role' claim", request.url.path)
        raise AppException(401, "Token missing role claim", error_code="TOKEN_MISSING_ROLE")

    try:
        public_id = str(sub)
    except (TypeError, ValueError):
        logger.warning("Auth failure [%s]: invalid user id '%s' in token", request.url.path, sub)
        raise AppException(401, "Invalid user id in token", error_code="TOKEN_INVALID_USER_ID")
    
    # Try to validate if public_id is a valid UUID format before querying
    try:
        uuid.UUID(public_id)
        is_valid_uuid = True
    except (ValueError, AttributeError):
        is_valid_uuid = False

    user = None
    if is_valid_uuid:
        user = await user_service.get_user_by_public_id(public_id)

    

    return CurrentUser(id=user.id, role=role)



async def require_role(current_user: CurrentUser = Depends(get_current_user), required_roles: list[UserRole] = None):
    """Dependency that checks if the current user has one of the required roles.
    
    Args:
        current_user: The current authenticated user
        required_roles: List of allowed roles. If None, allows all authenticated users.
        
    Raises:
        AppException(403): If user doesn't have required role
    """
    if required_roles is None:
        return current_user
    
    user_role = current_user.user_type
    
    # Convert UserRole enum to string if needed
    if isinstance(user_role, UserRole):
        user_role = user_role.value
    
    allowed_roles = [role.value if isinstance(role, UserRole) else role for role in required_roles]
    
    if user_role not in allowed_roles:
        logger.warning(
            "Access denied [%s]: user %s with role '%s' tried to access endpoint requiring roles: %s",
            "unknown", current_user.public_id, user_role, allowed_roles
        )
        raise AppException(
            403,
            f"Access denied. Required role: one of {allowed_roles}",
            error_code="INSUFFICIENT_PERMISSIONS"
        )
    
    return current_user


async def require_admin(current_user: CurrentUser = Depends(get_current_user)):
    """Dependency that requires admin role."""
    return await require_role(current_user, [UserRole.ADMIN])

async def require_vendor(current_user: CurrentUser = Depends(get_current_user)):
    """Dependency that requires vendor role."""
    return await require_role(current_user, [UserRole.VENDOR])

async def require_admin_or_vendor(current_user: CurrentUser = Depends(get_current_user)):
    """Dependency that requires either admin or vendor role."""
    return await require_role(current_user, [UserRole.ADMIN, UserRole.VENDOR])

async def require_user(current_user: CurrentUser = Depends(get_current_user)):
    """Dependency that requires either  user role."""
    return await require_role(current_user, [UserRole.USER])