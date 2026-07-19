import mimetypes
from typing import List
from uuid import uuid4

from app.application.dto.setting import SettingUpdateDTO
from app.deps.auth import CurrentUser
from app.schemas.setting_schema import SettingSchema
from app.services.setting_service import SettingNotFoundError, SettingService
from app.services.storage_service import StorageService


class UpdateSettingUseCase:
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
            self._delete_replaced_file(old_setting, payload["app_logo"])
            payload["app_logo"] = await self._upload_file(
                payload["app_logo"], folder="settings", field_name="app_logo"
            )
        
        if self._is_upload_file(payload.get("white_logo")):
            try:
                old_setting = await self.setting_service.get_by_key("white_logo")
            except SettingNotFoundError:
                old_setting = None
            self._delete_replaced_file(old_setting, payload["white_logo"]) 
            payload["white_logo"] = await self._upload_file(
                payload["white_logo"], folder="settings", field_name="white_logo"
            )

        if self._is_upload_file(payload.get("app_favicon")):
            try:
                old_setting = await self.setting_service.get_by_key("app_favicon")
            except SettingNotFoundError:
                old_setting = None
            self._delete_replaced_file(old_setting, payload["app_favicon"])
            payload["app_favicon"] = await self._upload_file(
                payload["app_favicon"], folder="settings", field_name="app_favicon"
            )

        if self._is_upload_file(payload.get("coming_background_image")):
            try:
                old_setting = await self.setting_service.get_by_key("coming_background_image")
            except SettingNotFoundError:
                old_setting = None
            self._delete_replaced_file(old_setting, payload["coming_background_image"])
            payload["coming_background_image"] = await self._upload_file(
                payload["coming_background_image"], folder="settings", field_name="coming_background_image"
            )

        
        if self._is_upload_file(payload.get("coming_soon_video")):
            try:
                old_setting = await self.setting_service.get_by_key("coming_soon_video")
            except SettingNotFoundError:
                old_setting = None
            self._delete_replaced_file(old_setting, payload["coming_soon_video"])
            payload["coming_soon_video"] = await self._upload_file(
                payload["coming_soon_video"], folder="settings", field_name="coming_soon_video"
            )

        saved_settings = {}
        for key, value in payload.items():
            if value is None:
                continue
            saved_settings[key] = await self.setting_service.upsert(key, value)

        if saved_settings.get("app_logo"):
            saved_settings["app_logo"] = SettingSchema(
                name="app_logo", value= self.storage_service.generate_presigned_url(saved_settings["app_logo"].value)    
            )
        
        if saved_settings.get("white_logo"):
            saved_settings["white_logo"] = SettingSchema(
                name="white_logo", value= self.storage_service.generate_presigned_url(saved_settings["white_logo"].value)    
            )

        if saved_settings.get("app_favicon"):
            saved_settings["app_favicon"] = SettingSchema(
                name="app_favicon", value= self.storage_service.generate_presigned_url(saved_settings["app_favicon"].value)    
            )

        if saved_settings.get("coming_background_image"):
            saved_settings["coming_background_image"] = SettingSchema(
                name="coming_background_image", value= self.storage_service.generate_presigned_url(saved_settings["coming_background_image"].value)    
            )

        if saved_settings.get("coming_soon_video"):
            saved_settings["coming_soon_video"] = SettingSchema(
                name="coming_soon_video", value= self.storage_service.generate_presigned_url(saved_settings["coming_soon_video"].value)    
            )

        if saved_settings.get("is_enabled_coming_soon"):
            saved_settings["is_enabled_coming_soon"] = SettingSchema(
                name="is_enabled_coming_soon", value= str(saved_settings["is_enabled_coming_soon"].value).lower()    
            )

        if saved_settings.get("coming_soon_message"):
            saved_settings["coming_soon_message"] = SettingSchema(
                name="coming_soon_message", value= saved_settings["coming_soon_message"].value    
            )

        if saved_settings.get("app_name"):
            saved_settings["app_name"] = SettingSchema(
                name="app_name", value= saved_settings["app_name"].value    
            )

        if saved_settings.get("app_timezone"):
            saved_settings["app_timezone"] = SettingSchema(
                name="app_timezone", value= saved_settings["app_timezone"].value    
            )

        if saved_settings.get("app_date_format"):
            saved_settings["app_date_format"] = SettingSchema(
                name="app_date_format", value= saved_settings["app_date_format"].value    
            )

        if saved_settings.get("app_time_format"):
            saved_settings["app_time_format"] = SettingSchema(
                name="app_time_format", value= saved_settings["app_time_format"].value    
            )

        return list(saved_settings.values())
    

    @staticmethod
    def _is_upload_file(value) -> bool:
        return hasattr(value, "read") and hasattr(value, "content_type")

    async def _upload_file(self, upload, *, folder: str, field_name: str) -> str:
        raw = await upload.read()
        mime_type = upload.content_type or mimetypes.guess_type(upload.filename or "")[0]
        extension = mimetypes.guess_extension(mime_type or "") or ""
        key = f"{folder}/{field_name}_{uuid4().hex}{extension}"
        return await self.storage_service.upload_bytes(key, raw, content_type=mime_type)

    async def _delete_replaced_file(self, old_setting, new_value):
        old_value = old_setting.value if old_setting else None
        if isinstance(old_value, str) and old_value and old_value != new_value:
            try:
                await self.storage_service.delete_object(old_value)
            except Exception:
                pass
