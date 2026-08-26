from datetime import datetime, timezone
import logging
from typing import Optional

from fastapi import Request, status
from user_agents import parse

from app.application.dto.auth import ResetPasswordDTO
from app.core.events import EventBus
from app.core.exceptions import AppException
from app.core.security import PasswordHasher, TokenManager
from app.events.events.users.password_update_notification import ResetPasswordEvent
from app.models.token_model import TokenType
from app.models.user_model import UserStatus
from app.services.ip_service import IpService
from app.services.token_service import TokenService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class ResetPasswordUseCase:
    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        verify_csrf: bool,
        event_bus: EventBus,
        ip_service: IpService,
    ):
        self.user_service = user_service
        self.token_service = token_service
        self.verify_csrf = verify_csrf
        self.event_bus = event_bus
        self.ip_service = ip_service
        self.token_manager = TokenManager()
        self.password_hasher = PasswordHasher()

    async def execute(self, data: ResetPasswordDTO, request: Request) -> dict:
        # Validate and decode JWT token signature and expiry
        await self.token_manager.decode_token(data.token)

        token = await self.token_service.get_by_token(data.token, flush=True)
        if not token:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Token not found",
                error_code="TOKEN_NOT_FOUND",
                field="token",
            )

        if token.type != TokenType.PASSWORD_RESET:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid token",
                error_code="INVALID_TOKEN_TYPE",
                field="token",
            )

        if token.is_revoked:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Password reset token has been revoked",
                error_code="REVOKED_PASSWORD_RESET_TOKEN",
                field="token",
            )

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Token has expired",
                error_code="TOKEN_EXPIRED",
                field="token",
            )

        if token.user_id is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found for token",
                error_code="USER_NOT_FOUND",
                field="token",
            )

        user = await self.user_service.get_user_by_id(token.user_id)
        if not user:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                error_code="USER_NOT_FOUND",
                field="user",
            )

        if user.status != UserStatus.ACTIVE:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Your account is not active. Please contact the administrator for assistance.",
                error_code="ACCOUNT_NOT_ACTIVE",
                field="email",
            )

        hashed_password = await self.password_hasher.hash_password(data.password)

        session = self.user_service.user_repository.db
        tx = session.begin_nested() if session.in_transaction() else session.begin()
        try:
            async with tx:
                await self.token_service.revoke_token(token, commit=False)
                user.password = hashed_password
                await self.user_service.update(user, commit=False)
        except AppException:
            raise
        except Exception as e:
            logger.error("Failed to reset password: %s", e, exc_info=True)
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to reset password",
                error_code="FAILED_TO_RESET_PASSWORD",
            )

        # Publish password update notification event
        client_ip = await self.ip_service.get_client_ip(request)
        user_agent_string = request.headers.get("user-agent", "")
        user_agent = parse(user_agent_string)
        ip_info = await self.ip_service.get_ip_details(client_ip)
        changed_at = datetime.now(timezone.utc)
        event = ResetPasswordEvent(
            payload={
                "email": user.email,
                "full_name": user.full_name,
                "changed_at": changed_at.strftime("%B %d, %Y at %I:%M %p UTC"),
                "device": f"{user_agent.browser.family} {user_agent.browser.version_string} on {user_agent.os.family} {user_agent.os.version_string}",
                "location": f"{ip_info.cityName if ip_info.cityName else 'Unknown'}, {ip_info.countryName if ip_info.countryName else 'Unknown'}" if ip_info else "Unknown",
                "ip_address": client_ip,
            }
        )
        await self.event_bus.publish(event)

        return {
            "message": "Password reset successfully",
            "user": {
                "id": str(user.public_id),
                "email": user.email,
                "full_name": user.full_name,
            },
        }

class CheckResetPasswordTokenUseCase:
    def __init__(
            self, 
            token_service: TokenService,
            verify_csrf: bool,
        ):
        self.token_service = token_service
        self.verify_csrf = verify_csrf
        self.token_manager = TokenManager()

    async def execute(self, token_str: str) -> bool:
        # Validate and decode JWT token signature and expiry
        decoded_token = await self.token_manager.decode_token(token_str)
        if decoded_token.get("type") != TokenType.PASSWORD_RESET:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid token type",
                error_code="INVALID_TOKEN_TYPE",
                field="token",
            )

        token = await self.token_service.get_by_token(token_str)
        if not token:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Token not found",
                error_code="TOKEN_NOT_FOUND",
                field="token",
            )

        if token.type != TokenType.PASSWORD_RESET:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid token type",
                error_code="INVALID_TOKEN_TYPE",
                field="token",
            )

        if token.is_revoked:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Password reset token has been revoked",
                error_code="REVOKED_PASSWORD_RESET_TOKEN",
                field="token",
            )

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Token has expired",
                error_code="TOKEN_EXPIRED",
                field="token",
            )

        return True
