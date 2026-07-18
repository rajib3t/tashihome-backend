from fastapi import Depends

from app.application.use_case.auth.login_use_case import LoginUseCase
from app.deps.service import get_ip_service, get_login_log_service, get_token_service, get_user_service
from app.services.ip_service import IpService
from app.services.login_log_service import LoginLogService
from app.services.token_service import TokenService
from app.services.user_service import UserService

# Dependency injection function to provide an instance of LoginUseCase with the required UserService, TokenService, and LoginLogService dependencies.
async def get_login_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    login_log_service: LoginLogService = Depends(get_login_log_service),
    ip_service: IpService = Depends(get_ip_service)  # Injecting IpService dependency
) -> LoginUseCase:
    # Return an instance of LoginUseCase, initialized with the provided UserService and TokenService.
    return LoginUseCase(user_service, token_service, login_log_service, ip_service)