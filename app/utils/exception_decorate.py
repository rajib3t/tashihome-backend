from functools import wraps
import inspect
import logging

from app.core.exceptions import AppException
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def handle_api_exceptions(func):

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except AppException:
            raise
        
        except HTTPException:
            raise

        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {e}")

            raise AppException(
                status_code=500,
                message="Internal server error",
                error_code="INTERNAL_SERVER_ERROR"
            )

    wrapper.__signature__ = inspect.signature(func)

    return wrapper