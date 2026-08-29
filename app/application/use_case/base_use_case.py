from uuid import uuid4
import mimetypes
from pathlib import Path
from datetime import date, datetime
from typing import Any
from app.core.exceptions import AppException

# Register common icon and image MIME types to ensure proper extension resolution
mimetypes.add_type("image/x-icon", ".ico")
mimetypes.add_type("image/vnd.microsoft.icon", ".ico")
mimetypes.add_type("image/ico", ".ico")
mimetypes.add_type("image/icon", ".ico")
mimetypes.add_type("image/x-ico", ".ico")


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
        return (
            value is not None
            and hasattr(value, "read")
            and hasattr(value, "content_type")
            and bool(getattr(value, "filename", None))
        )

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

        mime_type = upload.content_type or ""
        if not mime_type or mime_type == "application/octet-stream":
            guessed_type = mimetypes.guess_type(upload.filename or "")[0]
            if guessed_type:
                mime_type = guessed_type
            elif (upload.filename or "").lower().endswith(".ico"):
                mime_type = "image/x-icon"

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

    def _determine_extension(self, upload, mime_type: str, webp: bool = False) -> str:
        if webp:
            return ".webp"

        # 1. Prefer original extension from filename if valid
        filename = getattr(upload, "filename", None) or ""
        file_ext = Path(filename).suffix.lower()
        if file_ext in {
            ".ico", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif",
            ".mp4", ".mov", ".webm", ".pdf", ".txt", ".csv", ".json"
        }:
            return file_ext

        # 2. Known MIME types fallback
        known_mime_extensions = {
            "image/x-icon": ".ico",
            "image/vnd.microsoft.icon": ".ico",
            "image/ico": ".ico",
            "image/icon": ".ico",
            "image/x-ico": ".ico",
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
            "image/gif": ".gif",
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "video/quicktime": ".mov",
        }
        if mime_type in known_mime_extensions:
            return known_mime_extensions[mime_type]

        # 3. Guess extension from standard mimetypes
        guessed = mimetypes.guess_extension(mime_type) if mime_type else None
        if guessed:
            if guessed == ".cur" and ("icon" in mime_type or "ico" in mime_type):
                return ".ico"
            return guessed

        # 4. Fallback to filename extension
        if file_ext:
            return file_ext

        # 5. Fallback to MIME subtype
        if mime_type and "/" in mime_type:
            subtype = mime_type.split("/")[-1].split("+")[0]
            if subtype:
                return f".{subtype}"

        return ""

    async def _upload_file(self, upload, *, folder: str, field_name: str, webp: bool = False) -> str:
        raw, mime_type = await self._validate_upload_file(upload, field_name=field_name)
        extension = self._determine_extension(upload, mime_type, webp=webp)
        key = f"{folder}/{field_name}_{uuid4().hex}{extension}"
        if webp:
            return await self.storage_service.convert_and_upload_webp(key, raw, quality=82, lossless=False)
        return await self.storage_service.upload_bytes(key, raw, content_type=mime_type)

    async def _delete_replaced_file(self, old_setting, new_value):
        if old_setting is None:
            old_value = None
        elif isinstance(old_setting, str):
            old_value = old_setting
        else:
            old_value = old_setting.value
        if isinstance(old_value, str) and old_value:
            if old_value == new_value:
                return
            try:
                await self.storage_service.delete_object(old_value)
            except Exception:
                pass
