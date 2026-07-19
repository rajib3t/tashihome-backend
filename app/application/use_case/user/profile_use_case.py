from app.deps.auth import CurrentUser
from app.services.user_service import UserService
from app.schemas.user_schema import UserData

class ProfileUseCase:
    def __init__(
        self,
        user_service: UserService,
        current_user: CurrentUser
    ):
        self.user_service = user_service
        self.current_user = current_user
    
    async def execute(self) -> UserData:
       
       return await self.user_service.get_user_by_id(self.current_user.id)