from typing import List

from app.schemas.setting_schema import SettingSchema
from app.services.setting_service import SettingService
from app.services.storage_service import StorageService


class GetSettingUseCase:
    COMING_SOON_KEYS = {
        "coming_soon_message",
        "coming_background_image",
        "coming_soon_video",
        "launch_date",
    }

    def __init__(
        self,
        setting_service: SettingService,
        storage_service: StorageService,
    ):
        self.setting_service = setting_service
        self.storage_service = storage_service

    async def execute(self) -> List[SettingSchema]:
        settings = await self.setting_service.get_all()
        response: List[SettingSchema] = []
        coming_soon_enabled = False

        setting_map = {setting.key: setting.value for setting in settings}
        coming_soon_flag = setting_map.get("is_enabled_coming_soon")
        if isinstance(coming_soon_flag, str):
            coming_soon_enabled = coming_soon_flag.lower() == "true"

        for setting in settings:
            if not coming_soon_enabled and setting.key in self.COMING_SOON_KEYS:
                continue

            value = setting.value

            if setting.key in {
                "app_logo",
                "white_logo",
                "app_favicon",
                "coming_background_image",
                "coming_soon_video",
            }:
                value = value
            elif setting.key == "is_enabled_coming_soon":
                value = str(value).lower()

            response.append(
                SettingSchema(
                    name=setting.key,
                    value=value,
                )
            )

        return response

