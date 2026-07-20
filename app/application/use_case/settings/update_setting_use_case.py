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


class UpdateSettingUseCase:
    COMING_SOON_KEYS = {
        "coming_soon_message",
        "coming_background_image",
        "coming_soon_video",
        "launch_date",
    }

    FILE_UPLOAD_RULES = {
        "app_logo": {
            "allowed_prefixes": ("image/",),
            "max_size_bytes": 2 * 1024 * 1024,
        },
        "white_logo": {
            "allowed_prefixes": ("image/",),
            "max_size_bytes": 2 * 1024 * 1024,
        },
        "app_favicon": {
            "allowed_prefixes": ("image/",),
            "max_size_bytes": 1 * 1024 * 1024,
        },
        "coming_background_image": {
            "allowed_prefixes": ("image/",),
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
            await self._delete_replaced_file(old_setting, payload["app_logo"])
            payload["app_logo"] = await self._upload_file(
                payload["app_logo"], folder="settings", field_name="app_logo"
            )

        if self._is_upload_file(payload.get("white_logo")):
            try:
                old_setting = await self.setting_service.get_by_key("white_logo")
            except SettingNotFoundError:
                old_setting = None
            await self._delete_replaced_file(old_setting, payload["white_logo"])
            payload["white_logo"] = await self._upload_file(
                payload["white_logo"], folder="settings", field_name="white_logo"
            )

        if self._is_upload_file(payload.get("app_favicon")):
            try:
                old_setting = await self.setting_service.get_by_key("app_favicon")
            except SettingNotFoundError:
                old_setting = None
            await self._delete_replaced_file(old_setting, payload["app_favicon"])
            payload["app_favicon"] = await self._upload_file(
                payload["app_favicon"], folder="settings", field_name="app_favicon"
            )

        if self._is_upload_file(payload.get("coming_background_image")):
            try:
                old_setting = await self.setting_service.get_by_key("coming_background_image")
            except SettingNotFoundError:
                old_setting = None
            await self._delete_replaced_file(old_setting, payload["coming_background_image"])
            payload["coming_background_image"] = await self._upload_file(
                payload["coming_background_image"], folder="settings", field_name="coming_background_image"
            )

        if self._is_upload_file(payload.get("coming_soon_video")):
            try:
                old_setting = await self.setting_service.get_by_key("coming_soon_video")
            except SettingNotFoundError:
                old_setting = None
            await self._delete_replaced_file(old_setting, payload["coming_soon_video"])
            payload["coming_soon_video"] = await self._upload_file(
                payload["coming_soon_video"], folder="settings", field_name="coming_soon_video"
            )

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
                value = self.storage_service.generate_presigned_url(value)
            elif setting.key == "is_enabled_coming_soon":
                value = str(value).lower()

            response.append(
                SettingSchema(
                    name=setting.key,
                    value=value,
                )
            )

        return response

    @staticmethod
    def _normalize_payload_value(key: str, value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, bool):
            return str(value).lower()

        return value

    @staticmethod
    def _is_upload_file(value) -> bool:
        return hasattr(value, "read") and hasattr(value, "content_type")

    async def _validate_upload_file(self, upload, *, field_name: str) -> tuple[bytes, str]:
        if not self._is_upload_file(upload):
            raise AppException(
                status_code=400,
                message="File is not valid format",
                error_code="INVALID_FILE",
                field=field_name,
            )

        raw = await upload.read()
        if not raw:
            raise AppException(
                status_code=400,
                message="File is empty",
                error_code="INVALID_FILE",
                field=field_name,
            )

        mime_type = upload.content_type or mimetypes.guess_type(upload.filename or "")[0] or ""
        if not mime_type:
            raise AppException(
                status_code=400,
                message="File type is not supported",
                error_code="UNSUPPORTED_FILE_TYPE",
                field=field_name,
            )

        rules = self.FILE_UPLOAD_RULES.get(field_name)
        if rules is None:
            return raw, mime_type

        allowed_prefixes = rules["allowed_prefixes"]
        if not any(mime_type.startswith(prefix) for prefix in allowed_prefixes):
            raise AppException(
                status_code=400,
                message="File type is not supported",
                error_code="UNSUPPORTED_FILE_TYPE",
                field=field_name,
            )

        max_size_bytes = rules["max_size_bytes"]
        if len(raw) > max_size_bytes:
            raise AppException(
                status_code=413,
                message=f"{field_name} must be smaller than {max_size_bytes // (1024 * 1024)}MB.",
                error_code="FILE_TOO_LARGE",
                field=field_name,
            )

        return raw, mime_type

    async def _upload_file(self, upload, *, folder: str, field_name: str) -> str:
        raw, mime_type = await self._validate_upload_file(upload, field_name=field_name)
        extension = mimetypes.guess_extension(mime_type or "") or ""
        key = f"{folder}/{field_name}_{uuid4().hex}{extension}"
        return await self.storage_service.upload_bytes(key, raw, content_type=mime_type)

    async def _delete_replaced_file(self, old_setting, new_value):
        old_value = old_setting.value if old_setting else None
        if isinstance(old_value, str) and old_value:
            try:
                await self.storage_service.delete_object(old_value)
            except Exception:
                pass
