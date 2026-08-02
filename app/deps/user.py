from app.application.use_case.user.profile_use_case import ProfileUseCase
from app.deps.auth import CurrentUser, get_current_user
from app.services.user_service import UserService
from fastapi import Depends
from app.deps.service import get_user_service

async def get_user_profile_use_case(
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_user)
) -> ProfileUseCase:
    return ProfileUseCase(user_service, current_user)


