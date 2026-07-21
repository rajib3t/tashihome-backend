from fastapi.params import Depends

from app.application.use_case.settings.get_setting_use_case import GetSettingUseCase
from app.application.use_case.settings.update_setting_use_case import UpdateSettingUseCase
from app.deps.auth import CurrentUser, get_current_user, require_admin
from app.deps.service import get_setting_service, get_storage_service
from app.services.setting_service import SettingService
from app.services.storage_service import StorageService


async def get_get_setting_use_case(
    setting_service: SettingService = Depends(get_setting_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> GetSettingUseCase:
    return GetSettingUseCase(
        setting_service=setting_service,
        storage_service=storage_service,
    )


async def get_update_setting_use_case(
    setting_service: SettingService = Depends(get_setting_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateSettingUseCase:
    return UpdateSettingUseCase(
        setting_service=setting_service,
        storage_service=storage_service,
        current_user=current_user
    )