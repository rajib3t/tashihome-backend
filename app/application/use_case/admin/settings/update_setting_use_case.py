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
        "meta_image": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg", "image/webp"),
            "max_size_bytes": 3 * 1024 * 1024,
        },
        "og_image": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg", "image/webp"),
            "max_size_bytes": 3 * 1024 * 1024,
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

        file_configs = [
            ("app_logo", True),
            ("white_logo", True),
            ("app_favicon", False),
            ("coming_background_image", False),
            ("coming_soon_video", False),
        ]

        for file_key, is_webp in file_configs:
            val = payload.get(file_key)
            if self._is_upload_file(val):
                try:
                    old_setting = await self.setting_service.get_by_key(file_key)
                except SettingNotFoundError:
                    old_setting = None
                new_file_key = await self._upload_file(
                    val, folder="settings", field_name=file_key, webp=is_webp
                )
                await self._delete_replaced_file(old_setting, new_file_key)
                payload[file_key] = new_file_key
            elif hasattr(val, "read") or val is None:
                # Discard empty UploadFile objects so we do not overwrite existing stored files
                payload[file_key] = None

        og_val = payload.get("og_image")
        meta_val = payload.get("meta_image")

        if self._is_upload_file(og_val):
            try:
                old_setting = await self.setting_service.get_by_key("og_image")
            except SettingNotFoundError:
                try:
                    old_setting = await self.setting_service.get_by_key("meta_image")
                except SettingNotFoundError:
                    old_setting = None
            new_file_key = await self._upload_file(
                og_val, folder="settings", field_name="og_image", webp=True
            )
            await self._delete_replaced_file(old_setting, new_file_key)
            payload["og_image"] = new_file_key
            if not self._is_upload_file(meta_val):
                payload["meta_image"] = new_file_key
        elif hasattr(og_val, "read"):
            payload["og_image"] = None

        if self._is_upload_file(meta_val):
            try:
                old_setting = await self.setting_service.get_by_key("meta_image")
            except SettingNotFoundError:
                try:
                    old_setting = await self.setting_service.get_by_key("og_image")
                except SettingNotFoundError:
                    old_setting = None
            new_file_key = await self._upload_file(
                meta_val, folder="settings", field_name="meta_image", webp=True
            )
            await self._delete_replaced_file(old_setting, new_file_key)
            payload["meta_image"] = new_file_key
            if payload.get("og_image") is None and not hasattr(og_val, "read"):
                payload["og_image"] = new_file_key
        elif hasattr(meta_val, "read"):
            payload["meta_image"] = None

        # Keep og_image and meta_image in sync if one is provided as string
        if payload.get("og_image") and not payload.get("meta_image"):
            payload["meta_image"] = payload["og_image"]
        elif payload.get("meta_image") and not payload.get("og_image"):
            payload["og_image"] = payload["meta_image"]

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
                "meta_image",
                "og_image",
                "coming_background_image",
                "coming_soon_video",
            }:
                if value and str(value).strip():
                    value = await self.storage_service.get_display_url(value)
                else:
                    value = None
            elif setting.key == "is_enabled_coming_soon":
                value = str(value).lower()

            response.append(
                SettingSchema(
                    name=setting.key,
                    value=value,
                )
            )

        resp_keys = {s.name for s in response}
        if "og_image" in resp_keys and "meta_image" not in resp_keys:
            og_item = next(s for s in response if s.name == "og_image")
            response.append(SettingSchema(name="meta_image", value=og_item.value))
        elif "meta_image" in resp_keys and "og_image" not in resp_keys:
            meta_item = next(s for s in response if s.name == "meta_image")
            response.append(SettingSchema(name="og_image", value=meta_item.value))

        return response

    
