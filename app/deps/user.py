from fastapi import Depends

from app.application.use_case.user.profile_use_case import ProfileUseCase
from app.application.use_case.user.update_password_use_case import UpdatePasswordUseCase
from app.application.use_case.user.update_profile_image_use_case import UpdateProfileImageUseCase
from app.application.use_case.user.update_profile_info_use_case import UpdateProfileInfoUseCase
from app.deps.auth import CurrentUser, get_current_user
from app.deps.service import get_storage_service, get_user_service
from app.services.storage_service import StorageService
from app.services.user_service import UserService


async def get_user_profile_use_case(
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> ProfileUseCase:
    return ProfileUseCase(user_service, current_user)


async def get_update_profile_info_use_case(
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> UpdateProfileInfoUseCase:
    return UpdateProfileInfoUseCase(user_service, current_user)


async def get_update_password_use_case(
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> UpdatePasswordUseCase:
    return UpdatePasswordUseCase(user_service, current_user)


async def get_update_profile_image_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> UpdateProfileImageUseCase:
    return UpdateProfileImageUseCase(user_service, storage_service, current_user)
