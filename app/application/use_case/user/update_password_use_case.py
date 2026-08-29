from app.application.dto.profile import UpdatePasswordDTO
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.deps.auth import CurrentUser
from app.models.user_model import User
from app.services.user_service import UserService


class UpdatePasswordUseCase:
    def __init__(
        self,
        user_service: UserService,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.current_user = current_user
        self.password_hasher = PasswordHasher()

    async def execute(self, data: UpdatePasswordDTO) -> User:
        user = await self.user_service.get_user_by_id(self.current_user.id)
        if user is None:
            raise AppException(
                status_code=404,
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        is_valid_current = await self.password_hasher.verify_password(
            data.current_password, user.password
        )
        if not is_valid_current:
            raise AppException(
                status_code=400,
                message="Current password is incorrect.",
                field="current_password",
                error_code="INVALID_CURRENT_PASSWORD",
            )

        hashed_password = await self.password_hasher.hash_password(data.new_password)
        user.password = hashed_password

        return await self.user_service.update(user, commit=True)

