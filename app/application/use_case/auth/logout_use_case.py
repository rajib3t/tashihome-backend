from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.token_model import TokenType
from app.services.token_service import TokenService


class LogoutUseCase(BaseUseCase):

    def __init__(
        self,
        token_service : TokenService,
        verify_csrf : bool ,
        current_user : CurrentUser
    ):

        self.token_service = token_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(self):
        if not self.current_user.id:
            AppException(
                status_code=401,
                message="User not authenticated.",
                error_code="USER_NOT_AUTHENTICATED"
            )

        tokens= await self.token_service.get_active_tokens_by_user_id_and_type( 
            user_id=self.current_user.id,
            token_type=TokenType.REFRESH,
            flush=True
            
        )

        res = False
        if tokens:
                for token in tokens:
                    await self.token_service.delete_token(token)
                    res = True
        return res