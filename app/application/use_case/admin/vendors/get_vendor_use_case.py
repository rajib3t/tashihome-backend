from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class GetVendorUseCase(BaseUseCase):

    def __init__(
            self,
            user_service : UserService,
            storage_service: StorageService,
            verify_csrf: bool,
            current_user: CurrentUser
    ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user


    async def execute(
            self,
            user_id : str,
            data
    ): 
        pass