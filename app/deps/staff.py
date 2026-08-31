from fastapi import Depends

from app.application.use_case.admin.staffs.create_staff_use_case import CreateStaffUseCase
from app.application.use_case.admin.staffs.get_staff_use_case import GetStaffUseCase
from app.application.use_case.admin.staffs.list_staff_use_case import ListStaffUseCase
from app.application.use_case.admin.staffs.send_password_reset_link_use_case import (
    SendStaffPasswordResetLinkUseCase,
)
from app.application.use_case.admin.staffs.update_staff_use_case import (
    UpdateStaffUseCase,
    UpdateStatusStaffUseCase,
    UploadStaffProfileImageUseCase,
)
from app.core.csrf import verify_csrf
from app.core.events import EventBus
from app.deps.auth import CurrentUser, require_admin
from app.deps.event_bus import get_event_bus
from app.deps.service import (
    get_storage_service,
    get_token_service,
    get_user_service,
)
from app.services.storage_service import StorageService
from app.services.token_service import TokenService
from app.services.user_service import UserService


# =========================================================================
# Admin Staff Management Dependencies (Only accessible by Admin role)
# =========================================================================

async def get_admin_list_staff_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> ListStaffUseCase:
    return ListStaffUseCase(
        user_service=user_service,
        storage_service=storage_service,
        current_user=current_user,
    )


async def get_admin_get_staff_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> GetStaffUseCase:
    return GetStaffUseCase(
        user_service=user_service,
        storage_service=storage_service,
        current_user=current_user,
    )


async def get_admin_create_staff_use_case(
    user_service: UserService = Depends(get_user_service),
    event_bus: EventBus = Depends(get_event_bus),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
) -> CreateStaffUseCase:
    return CreateStaffUseCase(
        user_service=user_service,
        event_bus=event_bus,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_admin_update_staff_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateStaffUseCase:
    return UpdateStaffUseCase(
        user_service=user_service,
        storage_service=storage_service,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_admin_update_staff_status_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateStatusStaffUseCase:
    return UpdateStatusStaffUseCase(
        user_service=user_service,
        storage_service=storage_service,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_admin_upload_staff_profile_image_use_case(
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
) -> UploadStaffProfileImageUseCase:
    return UploadStaffProfileImageUseCase(
        user_service=user_service,
        storage_service=storage_service,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )


async def get_admin_send_staff_password_reset_link_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    event_bus: EventBus = Depends(get_event_bus),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
) -> SendStaffPasswordResetLinkUseCase:
    return SendStaffPasswordResetLinkUseCase(
        user_service=user_service,
        token_service=token_service,
        event_bus=event_bus,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )

