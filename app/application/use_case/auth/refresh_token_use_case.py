


from datetime import datetime, timedelta, timezone

from app.core.exceptions import AppException
from app.core.security import Token, TokenManager
from app.models.token_model import TokenType
from app.schemas.token_schema import TokenDataSchema
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
class RefreshTokenUseCase:
    def __init__(
            self, 
            user_service: UserService, 
            token_service: TokenService
        ):
        self.user_service = user_service
        self.token_service = token_service
        self.token_manager = TokenManager()  # Initialize the TokenManager instance

    async def execute(self, refresh_token: str) -> TokenDataSchema:
        # Validate the refresh token
        token_data = await self.token_manager.decode_token(refresh_token)
        logger.info(f"Decoded token data: {token_data}")
        if token_data["type"] != TokenType.REFRESH:
            raise AppException(
                status_code=400,
                message="Invalid token type.",
                error_code="INVALID_TOKEN_TYPE"
            )
        
        # Check if the token is revoked
        token_record = await self.token_service.get_by_token(refresh_token, with_relations=None, flush=True)
        if not token_record or token_record.is_revoked:
            raise AppException(
                status_code=401,
                message="Refresh token is revoked or invalid.",
                error_code="TOKEN_REVOKED_OR_INVALID"
            )
        
        # Get the user associated with the token
        user = await self.user_service.get_user_by_public_id(token_data["sub"])
        if not user:
            raise AppException(
                status_code=404,
                message="User not found.",
                error_code="USER_NOT_FOUND"
            )
        
        # Generate new access token
        access_token = await self.token_manager.create_access_token(
            data={"sub": str(user.public_id)},
            additional_claims={"role": user.role},
        )

        if token_record.expires_at < datetime.now(timezone.utc):
            # If the refresh token is expired, revoke it and generate a new one
            await self.token_service.revoke_token(token_record, commit=False)
            new_refresh_token = await self.token_manager.create_refresh_token(
                data={"sub": str(user.public_id)},
                additional_claims={
                    "email": user.email,
                    "role": user.role,
                },
            )
            new_token = Token(
                user_id=user.id,
                type=TokenType.REFRESH,
                token=new_refresh_token,
                expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )
            await self.token_service.create(
                new_token,
                with_relations=None,
                commit=True
            )
            return TokenDataSchema(
                access_token={
                    "type": TokenType.ACCESS,
                    "token": access_token
                },
                refresh_token=new_refresh_token
            )
        else:
            # If the refresh token is still valid, return the new access token and the existing refresh token
            return TokenDataSchema(
                access_token={
                    "type": TokenType.ACCESS,
                    "token": access_token
                },
                refresh_token=refresh_token 
            )
