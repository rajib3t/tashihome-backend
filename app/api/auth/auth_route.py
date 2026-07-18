from urllib import request

from fastapi import APIRouter, Depends, Request, Response

from app.api.base_controller import BaseController
from app.application.dto.auth import AuthDTO
from app.application.dto.auth import AuthDTO
from app.application.use_case.auth.login_use_case import LoginUseCase
from app.deps.auth import get_login_use_case
from app.schemas.auth_schema import LoginResponse, LoginResponseData
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
        login_response = LoginResponseData(
            user=login_data.user,
            token=login_data.token.access_token
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
        use_case: LoginUseCase = Depends(get_login_use_case),
    ):
        # Implement your refresh token logic here
        refresh_token = request.headers.get("Authorization")
        if not refresh_token:
            return self.build_response(
                message="Refresh token is missing",
                status_code=400
            )
        
        # Assuming you have a method to validate and refresh the token
        new_tokens = await use_case.refresh_token(refresh_token)
        
        return self.build_response(
            message="Token refreshed successfully",
            data=new_tokens
        )

    

controller = AuthController()
router = controller.router