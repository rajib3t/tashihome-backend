from app.application.use_case.base_use_case import BaseUseCase
import mimetypes
from datetime import date, datetime
from typing import Any, List
from uuid import uuid4

from app.application.dto.setting import SettingUpdateDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.schemas.setting_schema import SettingSchema
from app.services.setting_service import SettingNotFoundError, SettingService
from app.services.storage_service import StorageService


class UpdateSettingUseCase(BaseUseCase):
    COMING_SOON_KEYS = {
        "coming_soon_message",
        "coming_background_image",
        "coming_soon_video",
        "launch_date",
    }

    FILE_UPLOAD_RULES = {
        "app_logo": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/svg+xml"),
            "max_size_bytes": 2 * 1024 * 1024,
        },
        "white_logo": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/svg+xml"),
            "max_size_bytes": 2 * 1024 * 1024,
        },
        "app_favicon": {
            "allowed_prefixes": (
                "image/png",
                "image/x-icon",
                "image/ico",
                "image/icon",
                "image/vnd.microsoft.icon",
                "image/x-ico",
                "image/svg+xml",
                "image/jpeg",
                "image/jpg",
                "image/webp",
            ),
            "max_size_bytes": 1 * 1024 * 1024,
        },
        "coming_background_image": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg", "image/webp"),
            "max_size_bytes": 4 * 1024 * 1024,
        },
        "coming_soon_video": {
            "allowed_prefixes": ("video/",),
            "max_size_bytes": 10 * 1024 * 1024,
        },
    }

    def __init__(
            self,
            setting_service: SettingService,
            storage_service: StorageService,
            current_user: CurrentUser
        ):
        self.setting_service = setting_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, setting_update_dto: SettingUpdateDTO) -> List[SettingSchema]:
        payload = dict(setting_update_dto)

        if self._is_upload_file(payload.get("app_logo")):
            try:
                old_setting = await self.setting_service.get_by_key("app_logo")
            except SettingNotFoundError:
                old_setting = None
            new_file_key = await self._upload_file(
                payload["app_logo"], folder="settings", field_name="app_logo", webp=True
            )
            await self._delete_replaced_file(old_setting, new_file_key)
            payload["app_logo"] = new_file_key

        if self._is_upload_file(payload.get("white_logo")):
            try:
                old_setting = await self.setting_service.get_by_key("white_logo")
            except SettingNotFoundError:
                old_setting = None
            new_file_key = await self._upload_file(
                payload["white_logo"], folder="settings", field_name="white_logo", webp=True
            )
            await self._delete_replaced_file(old_setting, new_file_key)
            payload["white_logo"] = new_file_key

        if self._is_upload_file(payload.get("app_favicon")):
            try:
                old_setting = await self.setting_service.get_by_key("app_favicon")
            except SettingNotFoundError:
                old_setting = None
            new_file_key = await self._upload_file(
                payload["app_favicon"], folder="settings", field_name="app_favicon"
            )
            await self._delete_replaced_file(old_setting, new_file_key)
            payload["app_favicon"] = new_file_key

        if self._is_upload_file(payload.get("coming_background_image")):
            try:
                old_setting = await self.setting_service.get_by_key("coming_background_image")
            except SettingNotFoundError:
                old_setting = None
            new_file_key = await self._upload_file(
                payload["coming_background_image"], folder="settings", field_name="coming_background_image"
            )
            await self._delete_replaced_file(old_setting, new_file_key)
            payload["coming_background_image"] = new_file_key

        if self._is_upload_file(payload.get("coming_soon_video")):
            try:
                old_setting = await self.setting_service.get_by_key("coming_soon_video")
            except SettingNotFoundError:
                old_setting = None
            new_file_key = await self._upload_file(
                payload["coming_soon_video"], folder="settings", field_name="coming_soon_video"
            )
            await self._delete_replaced_file(old_setting, new_file_key)
            payload["coming_soon_video"] = new_file_key

        for key, value in payload.items():
            if value is None:
                continue
            normalized_value = self._normalize_payload_value(key, value)
            await self.setting_service.upsert(key, normalized_value)

        return await self._build_settings_response()

    async def _build_settings_response(self) -> List[SettingSchema]:
        settings = await self.setting_service.get_all()
        response: List[SettingSchema] = []
        setting_map = {setting.key: setting.value for setting in settings}
        coming_soon_enabled = False

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
                value = await self.storage_service.get_display_url(value)
            elif setting.key == "is_enabled_coming_soon":
                value = str(value).lower()

            response.append(
                SettingSchema(
                    name=setting.key,
                    value=value,
                )
            )

        return response

    
