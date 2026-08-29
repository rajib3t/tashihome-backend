from app.application.dto.profile import UpdateProfileInfoDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import User
from app.services.user_service import UserService


class UpdateProfileInfoUseCase:
    def __init__(
        self,
        user_service: UserService,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.current_user = current_user

    async def execute(self, data: UpdateProfileInfoDTO) -> User:
        user = await self.user_service.get_user_by_id(self.current_user.id)
        if user is None:
            raise AppException(
                status_code=404,
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        if data.phone is not None and data.phone != user.phone:
            existing_user = await self.user_service.get_user_by_phone(data.phone)
            if existing_user and existing_user.id != user.id:
                raise AppException(
                    status_code=409,
                    message="Phone number already in use by another account.",
                    field="phone",
                    error_code="PHONE_ALREADY_EXISTS",
                )
            user.phone = data.phone

        if data.full_name is not None:
            user.full_name = data.full_name

        if data.is_subscribed is not None:
            user.is_subscribed = data.is_subscribed

        return await self.user_service.update(user, commit=True)

