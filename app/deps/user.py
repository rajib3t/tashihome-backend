from fastapi import Depends

from app.application.use_case.admin.users.create_user_use_case import CreateUserUseCase
from app.application.use_case.admin.users.get_user_use_case import GetUserUseCase
from app.application.use_case.admin.users.list_user_use_case import ListUserUseCase
from app.application.use_case.admin.users.send_password_reset_link_use_case import (
    SendUserPasswordResetLinkUseCase,
)
from app.application.use_case.admin.users.update_user_use_case import (
    UpdateStatusUserUseCase,
    UpdateUserUseCase,
    UploadUserProfileImageUseCase,
)
from app.application.use_case.user.become_host_use_case import BecomeHostUseCase
from app.application.use_case.user.profile_use_case import ProfileUseCase
from app.application.use_case.user.update_password_use_case import UpdatePasswordUseCase
from app.application.use_case.user.update_profile_image_use_case import UpdateProfileImageUseCase
from app.application.use_case.user.update_profile_info_use_case import UpdateProfileInfoUseCase
from app.core.csrf import verify_csrf
from app.core.events import EventBus
from app.deps.auth import CurrentUser, get_current_user, require_admin, require_admin_or_staff
from app.deps.event_bus import get_event_bus
from app.deps.service import (
    get_address_service,
    get_company_service,
    get_storage_service,
    get_token_service,
    get_user_service,
)
from app.services.address_service import AddressService
from app.services.company_service import CompanyService
from app.services.storage_service import StorageService
from app.services.token_service import TokenService
from app.services.user_service import UserService


async def get_become_host_use_case(
    user_service: UserService = Depends(get_user_service),
    company_service: CompanyService = Depends(get_company_service),
    address_service: AddressService = Depends(get_address_service),
    event_bus: EventBus = Depends(get_event_bus),
    current_user: CurrentUser = Depends(get_current_user),
) -> BecomeHostUseCase:
    return BecomeHostUseCase(
        user_service=user_service,
        company_service=company_service,
        address_service=address_service,
        event_bus=event_bus,
        current_user=current_user,
    )



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


# =========================================================================
# Admin User Management Dependencies
# =========================================================================

async def get_admin_list_user_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> ListUserUseCase:
    return ListUserUseCase(
        user_service=user_service,
        storage_service=storage_service,
        current_user=current_user,
    )


async def get_admin_get_user_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> GetUserUseCase:
    return GetUserUseCase(
        user_service=user_service,
        storage_service=storage_service,
        current_user=current_user,
    )


async def get_admin_create_user_use_case(
    user_service: UserService = Depends(get_user_service),
    event_bus: EventBus = Depends(get_event_bus),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> CreateUserUseCase:
    return CreateUserUseCase(
        user_service=user_service,
        event_bus=event_bus,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_admin_update_user_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> UpdateUserUseCase:
    return UpdateUserUseCase(
        user_service=user_service,
        storage_service=storage_service,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_admin_update_user_status_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> UpdateStatusUserUseCase:
    return UpdateStatusUserUseCase(
        user_service=user_service,
        storage_service=storage_service,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_admin_upload_user_profile_image_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> UploadUserProfileImageUseCase:
    return UploadUserProfileImageUseCase(
        user_service=user_service,
        storage_service=storage_service,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_admin_send_password_reset_link_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    event_bus: EventBus = Depends(get_event_bus),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> SendUserPasswordResetLinkUseCase:
    return SendUserPasswordResetLinkUseCase(
        user_service=user_service,
        token_service=token_service,
        event_bus=event_bus,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )

