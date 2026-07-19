from urllib import request

from fastapi import APIRouter, Depends, Request, Response

from app.api.base_controller import BaseController
from app.application.dto.auth import AuthDTO
from app.application.dto.auth import AuthDTO
from app.application.use_case.auth.login_use_case import LoginUseCase
from app.application.use_case.auth.refresh_token_use_case import RefreshTokenUseCase
from app.deps.auth import get_login_use_case, get_refresh_token_use_case
from app.models.token_model import TokenType
from app.schemas.auth_schema import LoginResponse, LoginResponseData, RefreshTokenResponse
from app.schemas.token_schema import AccessTokenSchema
from app.utils.exception_decorate import handle_api_exceptions


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
            ("post", "/refresh-token", self._refresh_token, {"response_model": RefreshTokenResponse, "response_model_by_alias": False}),
        ]


        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)


    @handle_api_exceptions
    async def _login(
        self,
        request: Request,
        data:AuthDTO,
        response: Response,
        use_case: LoginUseCase = Depends(get_login_use_case),
    ):
        # Implement your login logic here
        login_data = await use_case.execute(
            email=data.email,
            password=data.password,
            request=request
        )
        response.set_cookie(
                TokenType.REFRESH.value,
                login_data.token.refresh_token,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=60 * 60 * 24 * 7,
            )
        if data.rememberMe:
            response.set_cookie(
                TokenType.ACCESS.value,
                login_data.token.access_token,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=60 * 30,
            )
        login_response = LoginResponseData(
            user=login_data.user,
            token=login_data.token.access_token,
        )
        return self.build_response(
           message="Login successful",
           data=login_response
        )
    
    @handle_api_exceptions
    async def _refresh_token(
        self,
        request: Request,
        response: Response,
        use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case),
    ):
        # Implement your refresh token logic here
        refresh_token = request.cookies.get(TokenType.REFRESH.value)
        
        
        # Assuming you have a method to validate and refresh the token
        new_tokens = await use_case.execute(refresh_token)
        response.set_cookie(
            TokenType.ACCESS.value,
            new_tokens.access_token.token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=60 * 30,
        )
        response.set_cookie(
            TokenType.REFRESH.value,
            new_tokens.refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=60 * 60 * 24 * 7,
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
