from app.deps.auth import get_forgot_password_use_case, get_get_active_account_use_case, get_reset_password_use_case
from app.application.use_case.auth.forgot_password_use_case import ForgotPasswordUseCase
from app.application.use_case.auth.reset_password_use_case import ResetPasswordUseCase
from app.deps.auth import get_active_account_use_case
from app.application.use_case.auth.active_account_use_case import ActiveAccountUseCase, GetActiveAccountUseCase
import logging

from fastapi import APIRouter, Depends, Request, Response

from app.api.base_controller import BaseController
from app.application.dto.auth import AuthDTO, RegisterDTO, ForgotPasswordDTO, ResetPasswordDTO
from app.application.use_case.auth.login_use_case import LoginUseCase
from app.application.use_case.auth.logout_use_case import LogoutUseCase
from app.application.use_case.auth.refresh_token_use_case import RefreshTokenUseCase
from app.core.config import settings
from app.core.csrf import  verify_csrf
from app.deps.auth import get_login_use_case, get_logout_use_case, get_refresh_token_use_case, get_register_use_case
from app.models.token_model import TokenType
from app.schemas.auth_schema import LoginResponse, LoginResponseData, RefreshTokenResponse, RegisterResponse
from app.schemas.token_schema import AccessTokenSchema
from app.utils.exception_decorate import handle_api_exceptions
from app.application.use_case.auth.register_use_case import RegisterUseCase

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
            {
                "post": "register",
                "handler": self._register,
                "route_kwargs": {"response_model": RegisterResponse, "response_model_by_alias": False, "status_code": 201},
            },
            ("post", "/logout", self.logout, {"response_model": dict}),  # protect state-changing route
            (
                "post", "/activate-account/{token}", self._active_account,
                {
                    "response_model": dict
                }
            ),
            (
                "get", "/check-active-account/{token}", self._get_check_active_account,
                {
                    "response_model": dict
                }
            ),
            (
                "post", "/forgot-password", self._forgot_password, 
                {
                    "response_model": dict
                }
            ),
            (
                "post", "/reset-password", self._reset_password,
                {
                    "response_model": dict
                }
            )
        ]
        for route in routes:
            if isinstance(route, dict):
                method = route["post"]
                handler = route["handler"]
                route_kwargs = route.get("route_kwargs", {})
                # pyrefly: ignore [bad-unpacking]
                self.router.add_api_route(f"/{method}", handler, methods=["POST"], **route_kwargs)
            else:
                method, path, handler, route_kwargs = route
                self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    

    def _set_auth_cookie(self, response: Response, name: str, value: str, max_age: int) -> None:
        response.set_cookie(
            name,
            value,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite=settings.cookie_samesite,
            max_age=max_age,
            domain=settings.COOKIE_DOMAIN,
        )

    @handle_api_exceptions
    async def _register(
        self,  
        data: RegisterDTO, 
        use_case: RegisterUseCase = Depends(get_register_use_case)
    ):
        user = await use_case.execute(data)
        response_data = {
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
        }
        return self.build_response(message="Registration successful & Check your email for a verification link , it will expire in 24 hours.", data=response_data)
    
    @handle_api_exceptions
    async def _login(self, request: Request, data: AuthDTO, response: Response, use_case: LoginUseCase = Depends(get_login_use_case)):
        login_data = await use_case.execute(email=data.email, password=data.password, request=request)

        self._set_auth_cookie(response, TokenType.REFRESH.value, login_data.token.refresh_token, 60 * 60 * 24 * 7)
        if data.rememberMe:
            self._set_auth_cookie(response, TokenType.ACCESS.value, login_data.token.access_token, 60 * 30)

        

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

    @handle_api_exceptions
    async def logout(
        self, 
        response: Response,
        use_case: LogoutUseCase = Depends(get_logout_use_case)
    ):

        # Clear the authentication cookies
        response.delete_cookie(TokenType.ACCESS.value)
        response.delete_cookie(TokenType.REFRESH.value)
        # Optionally, you can also revoke the refresh token in your database or token store here
        response.delete_cookie("csrf_token")  # Clear CSRF token cookie if used
        user_logged_out = await use_case.execute()
        return self.build_response(message="Logout successful", data=None)


    @handle_api_exceptions
    async def _active_account(
        self,
        token:str,
        use_case: ActiveAccountUseCase = Depends(get_active_account_use_case)
    ): 
        user_data = await use_case.execute(token)
        return self.build_response("Account activated successfully", user_data)

    @handle_api_exceptions
    async def _get_check_active_account(
        self,
        token:str,
        use_case: GetActiveAccountUseCase = Depends(get_get_active_account_use_case)
    ): 
        user_data = await use_case.execute(token)
        return self.build_response("Account is active", user_data)
    
    @handle_api_exceptions
    async def _forgot_password(
        self,
        data:ForgotPasswordDTO,
        use_case: ForgotPasswordUseCase = Depends(get_forgot_password_use_case)
    ):
        await use_case.execute(data)
        return self.build_response("Password reset email sent successfully")    


    @handle_api_exceptions
    async def _reset_password(
        self,
        request: Request,
        data:ResetPasswordDTO,
        use_case: ResetPasswordUseCase = Depends(get_reset_password_use_case)
    ):
        await use_case.execute(data, request)
        return self.build_response("Password reset successfully")
controller = AuthController()
router = controller.router
