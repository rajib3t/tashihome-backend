


from app.core.exceptions import AppException
from app.core.security import TokenManager
from app.models.token_model import TokenType
from app.services.token_service import TokenService
from app.services.user_service import UserService


class RefreshTokenUseCase:
    def __init__(
            self, 
            user_service: UserService, 
            token_service: TokenService
        ):
        self.user_service = user_service
        self.token_service = token_service
        self.token_manager = TokenManager()  # Initialize the TokenManager instance

    def execute(self, refresh_token: str) :
        # Validate the refresh token
        token_data = self.token_manager.decode_token(refresh_token)
        if token_data["type"] != TokenType.REFRESH:
            raise AppException(
                status_code=400,
                detail="Invalid token type.",
                error_code="INVALID_TOKEN_TYPE"
            )
        
        # Check if the token is revoked
        token_record = self.token_service.get_by_token(refresh_token, with_relations=None, flush=True)
        if not token_record or token_record.is_revoked:
            raise AppException(
                status_code=401,
                detail="Refresh token is revoked or invalid.",
                error_code="TOKEN_REVOKED_OR_INVALID"
            )
        