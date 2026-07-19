from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request

from app.core.exceptions import AppException
from app.core.security import PasswordHasher, TokenManager
from app.models.login_log_model import LoginLog
from app.models.token_model import Token, TokenType
from app.models.user_model import UserStatus
from app.schemas.auth_schema import LoginData, LoginResponseData
from app.services.ip_service import IpService
from app.services.login_log_service import LoginLogService
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.core.config import settings
from user_agents import parse
class LoginUseCase:
    def __init__(
            self, 
            user_service: UserService,
            token_service: TokenService,
            login_log_service: LoginLogService,
            ip_service: IpService
        ):
        self.user_service = user_service
        self.token_service = token_service
        self.login_log_service = login_log_service
        self.ip_service = ip_service
        self.password_hasher = PasswordHasher()
        self.token_manager = TokenManager()
    async def execute(self, email: str, password: str, request: Request) -> LoginData:
        user = await self.user_service.get_user_by_email(email, with_relations=None, flush=True)
        
        if not user:
            raise AppException(
                status_code=404, 
                message="User not found with the provided email.",
                error_code="USER_NOT_FOUND"
            )
        
        if user.status != UserStatus.ACTIVE:
            raise AppException(
                status_code=403, 
                message="User account is not active.",
                error_code="USER_INACTIVE"
            )

        if not await self.password_hasher.verify_password(password, user.password):
            raise AppException(
                status_code=401, 
                message="Invalid password.",
                error_code="INVALID_PASSWORD"
            )
        
        access_token = await self.token_manager.create_access_token(
            data={"sub": str(user.public_id)},
            additional_claims={
                "role": user.role,
            },
        )

        refresh_token = await self.token_manager.create_refresh_token(
            data={"sub": str(user.public_id)},
            additional_claims={
                "email": user.email,
                "role": user.role,
            },
        )
        now = datetime.now(timezone.utc)

        token = Token(
            user_id=user.id,
            token=refresh_token,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            type=TokenType.REFRESH
        )
        await self.token_service.create(
            token,
            with_relations=None,
            commit=True
        )

        # Log the login attempt
        if settings.LOGIN_LOG_ENABLED:
            
            await self.log_login_attempt(user_id=user.id, request=request)

        return LoginData(
            user=user,
            token={
                "access_token": {
                    
                    "type": TokenType.ACCESS,
                    "token": access_token
                },
                "refresh_token": refresh_token,
                
            }
        )        

    
            

        

         

    async def log_login_attempt(self, user_id: int, request: Request):
        client_ip = await self.ip_service.get_client_ip(request)
        
        user_agent_string = request.headers.get("user-agent", "")
        user_agent = parse(user_agent_string)
        device_info = {
            "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}" if user_agent.browser else "Unknown",
            "os": f"{user_agent.os.family} {user_agent.os.version_string}" if user_agent.os else "Unknown",
            "device": user_agent.device.family if user_agent.device else "Unknown",
            "is_mobile": user_agent.is_mobile,
            "is_tablet": user_agent.is_tablet,
            "is_pc": user_agent.is_pc,
            "is_bot": user_agent.is_bot,
        }
        ip_info = await self.ip_service.get_ip_details(client_ip)

        if ip_info:
            
            login_log = LoginLog(
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent_string,
                country=ip_info.countryName if ip_info.countryName else None,
                city=ip_info.cityName if ip_info.cityName else None,
                device_info=device_info,
            )

            await self.login_log_service.log_login_attempt(login_log,commit=True) 
