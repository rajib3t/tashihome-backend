
from datetime import datetime, timezone
from typing import Optional
import logging

from fastapi import status

from app.core.exceptions import AppException
from app.core.security import TokenManager
from app.models.token_model import TokenType
from app.models.user_model import UserStatus
from app.services.token_service import TokenService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class ActiveAccountUseCase:
    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        verify_csrf: bool,
    ):
        self.user_service = user_service
        self.token_service = token_service
        self.verify_csrf = verify_csrf
        self.token_manager = TokenManager()

    async def execute(self, token: str) -> Optional[dict]:
        # Decode and validate JWT expiration and signature
        await self.token_manager.decode_token(token)

        token_obj = await self.token_service.get_by_token(token, flush=True)
        if not token_obj:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Token not found.",
                field="token",
                error_code="TOKEN_NOT_FOUND",
            )

        if token_obj.type != TokenType.ACCOUNT_ACTIVATION:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid token type.",
                error_code="INVALID_TOKEN_TYPE",
                field="token",
            )

        if token_obj.is_revoked:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Account activation token has been revoked",
                error_code="REVOKED_ACCOUNT_ACTIVATION_TOKEN",
                field="token",
            )

        expires_at = token_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Account activation token has expired",
                error_code="EXPIRED_ACCOUNT_ACTIVATION_TOKEN",
                field="token",
            )

        if token_obj.user_id is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found for verification",
                error_code="USER_NOT_FOUND",
                field="email",
            )

        user = await self.user_service.get_user_by_id(token_obj.user_id)
        if not user:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found.",
                field="user",
                error_code="USER_NOT_FOUND",
            )

        if user.status == UserStatus.ACTIVE:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="User is already verified",
                error_code="USER_ALREADY_VERIFIED",
                field="email",
            )

        session = self.user_service.user_repository.db
        tx = session.begin_nested() if session.in_transaction() else session.begin()
        try:
            async with tx:
                await self.token_service.revoke_token(token_obj, commit=False)
                user.status = UserStatus.ACTIVE
                await self.user_service.update(user, commit=False)
        except AppException:
            raise
        except Exception as e:
            logger.error("Failed to activate account: %s", e, exc_info=True)
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to activate account",
                error_code="FAILED_TO_ACTIVATE_ACCOUNT",
            )

        return {
            "user": {
                "id": user.public_id,
                "name": user.full_name,
                "email": user.email,
            },
        }


class GetActiveAccountUseCase:
    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        verify_csrf: bool,
    ):
        self.user_service = user_service
        self.token_service = token_service
        self.verify_csrf = verify_csrf
        self.token_manager = TokenManager()

    async def execute(self, token: str) -> Optional[dict]:
        # Activation revokes its persisted token. For this frontend status check,
        # use the signed JWT's public user ID rather than that revoked record.
        token_data = await self.token_manager.decode_token(token)
        if token_data.get("type") != TokenType.ACCOUNT_ACTIVATION:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid token type.",
                error_code="INVALID_TOKEN_TYPE",
                field="token",
            )

        public_id = token_data.get("sub")
        if not public_id:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Token does not contain a user identifier.",
                error_code="INVALID_TOKEN",
                field="token",
            )

        user = await self.user_service.get_user_by_public_id(public_id)
        if not user:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found.",
                field="user",
                error_code="USER_NOT_FOUND",
            )
        
        # An activated account can be reported immediately. Its activation token
        # is expected to be revoked by the activation endpoint.
        if user.status == UserStatus.ACTIVE:
            return {
                "user": {
                    "id": user.public_id,
                    "name": user.full_name,
                    "email": user.email,
                },
            }

        # For inactive accounts, verify that this is still a usable activation
        # token before allowing the frontend to continue the activation flow.
        token_obj = await self.token_service.get_by_token(token, flush=True)
        if not token_obj:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Token not found.",
                field="token",
                error_code="TOKEN_NOT_FOUND",
            )

        if token_obj.type != TokenType.ACCOUNT_ACTIVATION:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid token type.",
                error_code="INVALID_TOKEN_TYPE",
                field="token",
            )

        if token_obj.is_revoked:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Account activation token has been revoked",
                error_code="REVOKED_ACCOUNT_ACTIVATION_TOKEN",
                field="token",
            )

        expires_at = token_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Account activation token has expired",
                error_code="EXPIRED_ACCOUNT_ACTIVATION_TOKEN",
                field="token",
            )

        return {
            "user": {
                "id": user.public_id,
                "name": user.full_name,
                "email": user.email,
            },
        }
