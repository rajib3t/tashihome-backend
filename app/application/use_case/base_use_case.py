from uuid import uuid4
import mimetypes
from app.core.exceptions import AppException
from datetime import date, datetime
from sqlalchemy.dialects.postgresql import Any
class BaseUseCase:
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

    async def _upload_file(self, upload, *, folder: str, field_name: str, webp: bool = False) -> str:
        raw, mime_type = await self._validate_upload_file(upload, field_name=field_name)
        extension = mimetypes.guess_extension(mime_type or "") or ""
        key = f"{folder}/{field_name}_{uuid4().hex}{extension}"
        if webp:
            return await self.storage_service.convert_and_upload_webp(key, raw, quality=82, lossless=False)
        return await self.storage_service.upload_bytes(key, raw, content_type=mime_type)

    async def _delete_replaced_file(self, old_setting, new_value):
        old_value = old_setting.value if old_setting else None
        if isinstance(old_value, str) and old_value:
            try:
                await self.storage_service.delete_object(old_value)
            except Exception:
                pass