from brevo.balance.types import post_loyalty_balance_programs_pid_balance_definitions_request_balance_availability_duration_modifier
import logging
from typing import Any
from app.deps.service import get_email_service, get_storage_service
from app.deps.service import get_email_template_service
from app.models.token_model import TokenType
from app.services.email_template_service import EmailTemplateService
from app.core.security import TokenManager
from app.core.config import settings
from app.core.database import db as database
from app.repositories.token_repository import TokenRepository
from app.repositories.setting_repository import SettingRepository
from app.services.setting_service import SettingService
from app.models.token_model import Token
from datetime import timedelta
from datetime import timezone
from datetime import datetime
from datetime import date

logger = logging.getLogger(__name__)
class ForgotPasswordHandler:
    @staticmethod
    async def handle(payload: dict[str, Any]) -> None:
        user_id = payload["id"]
        email = payload["email"]
        public_id = str(payload["public_id"])
        password_reset_token = payload["password_reset_token"]
        expires_at = payload["expires_at"]


        if settings.FRONTEND_URL:
            active_link = settings.FRONTEND_URL.rstrip("/") + f"/password-reset/{password_reset_token}"
        else:
            active_link = f"Use this verification token to reset your password: {password_reset_token}"


        async with database.async_session() as session:
            setting_service = SettingService(SettingRepository(session))
            username = payload.get("full_name") or "User"
            current_year = date.today().year
            storage_service = get_storage_service()
            app_name_setting = await setting_service.get_by_key("app_name")
            logo_setting = await setting_service.get_by_key("app_logo")
            app_name = app_name_setting.value
            logo_url = (await storage_service.get_display_url(logo_setting.value)) if logo_setting else None
            values = {
                "logo_url": logo_url,
                "full_name": username,
                "activation_url": active_link,
                "expires_in": settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
                "app_name": app_name,
                "year": current_year,
            }
            email_template_service = await get_email_template_service()
            html_content = await email_template_service.render_template(
                "forgot_password_email",
                values,
                strict=True,
            )

            email_service = await get_email_service()
            try:
                await email_service.send_email(
                        to_email=email,
                        subject="Reset your password",
                        text=(
                        f"Hi {username},\n\n"
                        "Please reset your password by clicking the link below:\n\n"
                        f"{active_link}\n\n"
                        "If you did not request this, please ignore this email."
                    ),
                    html=html_content,
                )
                logger.info("Sent forgot password email to %s", email)
            except Exception as exc:
                logger.error(
                    "Failed to send forgot password emails for %s: %s",
                    email,
                    exc,
                    exc_info=True,
                )