from fastapi import UploadFile

from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import User
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class UpdateProfileImageUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "profile_image": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg", "image/webp"),
            "max_size_bytes": 2 * 1024 * 1024,  # 2 MB
        },
    }

    def __init__(
        self,
        user_service: UserService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, profile_image: UploadFile) -> User:
        user = await self.user_service.get_user_by_id(self.current_user.id)
        if user is None:
            raise AppException(
                status_code=404,
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        if not self._is_upload_file(profile_image):
            raise AppException(
                status_code=400,
                message="Profile image file is required.",
                field="profile_image",
                error_code="INVALID_FILE",
            )

        # Remove previous image if one exists
        if user.is_profile_image_url:
            await self._delete_replaced_file(user.is_profile_image_url, None)

        # Upload new image as WebP
        image_key = await self._upload_file(
            profile_image,
            folder="profiles",
            field_name="profile_image",
            webp=True,
        )

        user.is_profile_image_url = image_key
        return await self.user_service.update(user, commit=True)

    async def delete_image(self) -> User:
        user = await self.user_service.get_user_by_id(self.current_user.id)
        if user is None:
            raise AppException(
                status_code=404,
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        if user.is_profile_image_url:
            await self._delete_replaced_file(user.is_profile_image_url, None)
            user.is_profile_image_url = None
            return await self.user_service.update(user, commit=True)

        return user

