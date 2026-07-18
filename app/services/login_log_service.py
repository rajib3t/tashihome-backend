from typing import Optional

from app.models.login_log_model import LoginLog
from app.repositories.token_repository import TokenRepository


class LoginLogService:
    def __init__(self, login_log_repository: TokenRepository):
        self.login_log_repository = login_log_repository

    
    async def log_login_attempt(self, login_log : LoginLog, commit: bool = True) -> Optional[LoginLog]:
        # This method logs a login attempt for a user, including their user ID and IP address.
        await self.login_log_repository.create(login_log, commit=commit)

    