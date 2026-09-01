import re
from typing import Optional

from fastapi import Request

from app.core.exceptions import IdempotencyKeyRequiredError
from app.core.idempotency import extract_idempotency_key

UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


async def require_idempotency_key(request: Request) -> str:
    """
    FastAPI dependency to enforce that the client provides a valid Idempotency-Key header.
    Raises IdempotencyKeyRequiredError (400 Bad Request) if header is missing or empty.
    """
    key = extract_idempotency_key(request)
    if not key:
        raise IdempotencyKeyRequiredError(
            message="Idempotency-Key (or X-Idempotency-Key) header is required for this operation."
        )

    # Clean and length-check the key
    cleaned_key = key.strip()
    if len(cleaned_key) < 8 or len(cleaned_key) > 256:
        raise IdempotencyKeyRequiredError(
            message="Idempotency-Key must be between 8 and 256 characters in length (e.g. UUID v4)."
        )

    return cleaned_key


async def get_idempotency_key(request: Request) -> Optional[str]:
    """
    FastAPI dependency to optionally retrieve the Idempotency-Key if present.
    """
    return extract_idempotency_key(request)

