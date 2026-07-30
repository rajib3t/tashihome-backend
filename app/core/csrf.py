import hmac
import secrets

from fastapi import Request, Response
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings
from app.core.exceptions import AppException

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


def issue_csrf_cookie(response: Response) -> str:
    """Generate a fresh CSRF token and set it as a readable (non-httponly) cookie."""
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        CSRF_COOKIE_NAME,
        token,
        httponly=False,  # frontend JS must be able to read this one
        secure=settings.SECURE_COOKIES,
        samesite=settings.cookie_samesite,
        domain=settings.COOKIE_DOMAIN,
        max_age=60 * 60 * 24 * 7,
    )
    return token


async def verify_csrf(request: Request) -> None:
    """Dependency: enforce double-submit CSRF check on state-changing routes."""
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)

    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        raise AppException(
            status_code=HTTP_403_FORBIDDEN,
            message="CSRF token missing or invalid",
            error_code="CSRF_TOKEN_INVALID",
        )
