import base64
import mimetypes
import re
from dataclasses import dataclass
from typing import Optional

from app.core.exceptions import AppException


@dataclass(frozen=True)
class DataUrlFile:
    raw: bytes
    mime_type: str
    extension: str


DATA_URL_PATTERN = re.compile(
    r"^data:(?P<mime>[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+);base64,(?P<data>.+)$"
)


def validate_data_url_file(data_url: str, *, allowed_prefixes: Optional[tuple[str, ...]] = None) -> DataUrlFile:
    if not data_url or not isinstance(data_url, str):
        raise AppException(
            status_code=400,
            message="File is not valid format",
            error_code="INVALID_FILE",
            field="file",
        )

    match = DATA_URL_PATTERN.match(data_url.strip())
    if not match:
        raise AppException(
            status_code=400,
            message="File is not valid format",
            error_code="INVALID_FILE",
            field="file",
        )

    mime_type = match.group("mime")
    if allowed_prefixes and not mime_type.startswith(allowed_prefixes):
        raise AppException(
            status_code=400,
            message="File type is not supported",
            error_code="UNSUPPORTED_FILE_TYPE",
            field="file",
        )

    try:
        raw = base64.b64decode(match.group("data"))
    except Exception as exc:
        raise AppException(
            status_code=400,
            message="File data is not valid base64",
            error_code="INVALID_FILE",
            field="file",
        ) from exc

    extension = mimetypes.guess_extension(mime_type) or f".{mime_type.split('/')[-1]}"
    return DataUrlFile(raw=raw, mime_type=mime_type, extension=extension)