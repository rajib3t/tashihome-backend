import logging
from datetime import datetime, timedelta, timezone
from fastapi import status

from app.application.dto.users.user import UserResetLinkDTO
from app.core.config import settings
from app.core.events import EventBus
from app.core.exceptions import AppException
from app.core.security import TokenManager
from app.deps.auth import CurrentUser
from app.events.events.users.forgot_password_event import ForgotPasswordEvent
from app.models.token_model import Token, TokenType
from app.models.user_model import UserStatus
from app.services.token_service import TokenService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class SendUserPasswordResetLinkUseCase:
    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        event_bus: EventBus,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.token_service = token_service
        self.event_bus = event_bus
        self.verify_csrf = verify_csrf
        self.current_user = current_user
        self.token_manager = TokenManager()

    async def execute(self, user_id: str, data: UserResetLinkDTO):
        if data.confirm != "CONFIRM":
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Confirmation string does not match. Please provide the correct confirmation string ('CONFIRM') to proceed.",
                error_code="CONFIRMATION_STRING_MISMATCH",
                field="confirm",
            )

        user = await self.user_service.get_user_by_public_id(user_id)
        if not user:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                error_code="USER_NOT_FOUND",
                field="user_id",
            )

        if user.status != UserStatus.ACTIVE:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="User account is not active. Password reset link can only be sent to active accounts.",
                error_code="ACCOUNT_NOT_ACTIVE",
                field="email",
            )

        existing_tokens = await self.token_service.get_active_tokens_by_user_id_and_type(
            user_id=user.id,
            token_type=TokenType.PASSWORD_RESET,
        )

        for existing_token in existing_tokens:
            expires_at = existing_token.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
                await self.token_service.revoke_token(existing_token, commit=False)
                logger.info("Revoked expired password reset token for user %s", user.id)
            else:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Password reset email has already been sent. Please check email or try again later.",
                    error_code="RESET_EMAIL_ALREADY_SENT",
                    field="email",
                )

        password_reset_token = await self.token_manager.generate_reset_token(
            public_id=str(user.public_id),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES),
        )

        now = datetime.now(timezone.utc)
        token = Token(
            user_id=user.id,
            token=password_reset_token,
            expires_at=now + timedelta(minutes=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES),
            type=TokenType.PASSWORD_RESET,
        )

        token = await self.token_service.create(
            token,
            with_relations=None,
            commit=True,
        )

        try:
            await self.event_bus.publish(
                ForgotPasswordEvent(
                    {
                        "id": int(user.id),
                        "public_id": str(user.public_id),
                        "full_name": user.full_name,
                        "email": user.email,
                        "password_reset_token": password_reset_token,
                        "expires_at": token.expires_at.isoformat(),
                    }
                )
            )
        except Exception as exc:
            logger.warning("Failed to publish ForgotPasswordEvent for user %s: %s", user.id, exc)

        return {
            "message": "Password reset link sent successfully.",
        }

