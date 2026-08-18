from app.events.events.users.forgot_password_event import ForgotPasswordEvent
from app.models.user_model import UserStatus
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from fastapi import status

from app.core.exceptions import AppException
from app.core.security import TokenManager
from app.models.token_model import Token, TokenType
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.application.dto.auth import ForgotPasswordDTO
from app.core.events import EventBus
from app.core.config import settings

logger = logging.getLogger(__name__)

class ForgotPasswordUseCase:
    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        event_bus: EventBus,
        verify_csrf: bool,
    ):
        self.user_service = user_service
        self.token_service = token_service
        self.verify_csrf = verify_csrf
        self.event_bus = event_bus
        self.token_manager = TokenManager()
    async def execute(self, data: ForgotPasswordDTO):
        user =  await self.user_service.get_user_by_email(data.email)
        if not user:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                error_code="USER_NOT_FOUND",
                field="email",
            )
        
        if user.status != UserStatus.ACTIVE:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Your account is not active. Please contact the administrator for assistance.",
                error_code="ACCOUNT_NOT_ACTIVE",
                field="email",
            )

        # Check for existing active password reset tokens
        existing_tokens = await self.token_service.get_active_tokens_by_user_id_and_type(
            user_id=user.id,
            token_type=TokenType.PASSWORD_RESET
        )
        
        # Check existing password reset tokens
        for existing_token in existing_tokens:
            # Check if token is expired
            expires_at = existing_token.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < datetime.now(timezone.utc):
                # Token is expired, revoke it
                await self.token_service.revoke_token(existing_token, commit=False)
                logger.info(f"Revoked expired password reset token for user {user.id}")
            else:
                # Token is still within time limit, raise exception
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Password reset email has already been sent. Please check your email.",
                    error_code="RESET_EMAIL_ALREADY_SENT",
                    field="email",
                )
        
        # Generate new password reset token
        password_reset_token = await self.token_manager.generate_reset_token(
            public_id=str(user.public_id),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES)
        )
        
        # Create token record with expiration
        now = datetime.now(timezone.utc)
        token = Token(
            user_id=user.id,
            token=password_reset_token,
            expires_at=now + timedelta(minutes=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES),
            type=TokenType.PASSWORD_RESET
        )
        
        token = await self.token_service.create(
            token,
            with_relations=None,
            commit=True
        )
        
        # TODO: Send email with password reset link
        # This would typically use the event_bus to publish an event that triggers email sending
        
        try:
            await self.event_bus.publish(ForgotPasswordEvent({
                "id": int(user.id),
                "public_id": str(user.public_id),
                "full_name": user.full_name,
                "email": user.email,
                "password_reset_token": password_reset_token,
                "expires_at": token.expires_at.isoformat()
            }))
        except Exception as exc:
            logger.warning("Failed to publish ForgotPasswordEvent for user %s: %s", user.id, exc)

        return {
            "message": "Password reset link sent to your email",
            "token": token.token # In production, don't return the token
        }