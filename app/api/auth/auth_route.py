import logging

from fastapi import APIRouter, Depends, Request, Response

from app.api.base_controller import BaseController
from app.application.dto.auth import AuthDTO
from app.application.use_case.auth.login_use_case import LoginUseCase
from app.application.use_case.auth.refresh_token_use_case import RefreshTokenUseCase
from app.core.config import settings
from app.core.csrf import issue_csrf_cookie, verify_csrf
from app.deps.auth import get_login_use_case, get_refresh_token_use_case
from app.models.token_model import TokenType
from app.schemas.auth_schema import LoginResponse, LoginResponseData, RefreshTokenResponse
from app.schemas.token_schema import AccessTokenSchema
from app.utils.exception_decorate import handle_api_exceptions

logger = logging.getLogger(__name__)

class AuthController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/auth",
            tags=["Auth"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("post", "/login", self._login, {"response_model": LoginResponse, "response_model_by_alias": False}),
            (
                "post", "/refresh-token", self._refresh_token,
                {
                    "response_model": RefreshTokenResponse,
                    "response_model_by_alias": False,
                    "dependencies": [Depends(verify_csrf)],  # protect state-changing route
                },
            ),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)


    def _set_auth_cookie(self, response: Response, name: str, value: str, max_age: int) -> None:
        response.set_cookie(
            name,
            value,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite=settings.cookie_samesite,
            max_age=max_age,
        )


    @handle_api_exceptions
    async def _login(self, request: Request, data: AuthDTO, response: Response, use_case: LoginUseCase = Depends(get_login_use_case)):
        login_data = await use_case.execute(email=data.email, password=data.password, request=request)

        self._set_auth_cookie(response, TokenType.REFRESH.value, login_data.token.refresh_token, 60 * 60 * 24 * 7)
        if data.rememberMe:
            self._set_auth_cookie(response, TokenType.ACCESS.value, login_data.token.access_token, 60 * 30)

        issue_csrf_cookie(response)  # issue CSRF token on successful login

        login_response = LoginResponseData(user=login_data.user, token=login_data.token.access_token)
        return self.build_response(message="Login successful", data=login_response)
    
    @handle_api_exceptions
    async def _refresh_token(
        self,
        request: Request,
        response: Response,
        use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case),
    ):
        # Implement your refresh token logic here
        refresh_token = request.cookies.get(TokenType.REFRESH.value)
        
        logger.info("Refresh token received: %s", refresh_token)
        
        # Assuming you have a method to validate and refresh the token
        new_tokens = await use_case.execute(refresh_token)
        self._set_auth_cookie(
            response,
            TokenType.ACCESS.value,
            new_tokens.access_token.token,
            60 * 30,
        )
        self._set_auth_cookie(
            response,
            TokenType.REFRESH.value,
            new_tokens.refresh_token,
            60 * 60 * 24 * 7,
        )
        response_data = AccessTokenSchema(
            token=new_tokens.access_token.token,
            type=TokenType.ACCESS,
        )
            
        return self.build_response(
            
            message="Token refreshed successfully",
            data=response_data
        )

    

controller = AuthController()
router = controller.router
