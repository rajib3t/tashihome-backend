from fastapi.params import Depends

from app.deps.repository import get_token_repository, get_user_repository

from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.services import token_service
from app.services import user_service
from app.services.ip_service import IpService
from app.services.login_log_service import LoginLogService
from app.services.token_service import TokenService
from app.services.user_service import UserService

# Dependency injection function to provide an instance of UserService with the required UserRepository dependency.
async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    
    # Return an instance of UserService, initialized with the provided UserRepository.
    return UserService(user_repository) 

# Dependency injection function to provide an instance of TokenService with the required TokenRepository dependency.    
async def get_token_service(
    token_repository: TokenRepository = Depends(get_token_repository),
) -> TokenService:
    # Return an instance of TokenService, initialized with the provided TokenRepository.
    return TokenService(token_repository)

async def get_login_log_service(
    login_log_repository: TokenRepository = Depends(get_token_repository),
):
    # Return an instance of LoginLogService, initialized with the provided UserService and TokenService.
    return LoginLogService(login_log_repository)

# Dependency injection function to provide an instance of IpService.
async def get_ip_service():
    """Get the IP service."""
    return IpService()