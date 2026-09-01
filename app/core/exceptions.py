import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class AppException(HTTPException):

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        field: Optional[str] = None,
        errors: Optional[List[Dict[str, str]]] = None,
    ):
        self.message = message
        logger.warning("%s - %s", status_code, message)

        detail = {
            "status": "error",
            "message": message,
        }

        if error_code:
            detail["error_code"] = error_code

        # Multiple field errors
        if errors:
            detail["errors"] = errors

        # Single field error
        elif field:
            detail["errors"] = [
                {
                    "field": field,
                    "message": message
                }
            ]

        super().__init__(status_code=status_code, detail=detail)



class TokenInvalidError(AppException):
    def __init__(self, message: str = "Invalid token"):
        super().__init__(401, message, error_code="TOKEN_INVALID")

class TokenExpiredError(AppException):
    def __init__(self, message: str = "Token has expired"):
        super().__init__(401, message, error_code="TOKEN_EXPIRED")


class RateLimitExceededError(AppException):
    def __init__(
        self,
        message: str = "Too many requests. Your IP has been temporarily blocked for 1 hour.",
        retry_after: int = 3600,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=429,
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
        )
        self.retry_after = retry_after
        if details:
            self.detail["details"] = details
        if retry_after > 0:
            self.detail["retry_after"] = retry_after