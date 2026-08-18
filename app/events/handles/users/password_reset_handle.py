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
class ResetPasswordHandler:
    @staticmethod
    async def handle(payload: dict[str, Any]) -> None:
        


        if settings.FRONTEND_URL:
            active_link = settings.FRONTEND_URL.rstrip("/") + f"/login"
        else:
            active_link = "Update your password"


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
                "secure_account_url":active_link,
                "app_name": app_name,
                "year": current_year,
                "changed_at": payload.get("changed_at"),
                "device": payload.get("device"),
                "location": payload.get("location"),
                "ip_address": payload.get("ip_address"),
            }
            email_template_service = await get_email_template_service()
            html_content = await email_template_service.render_template(
                "password_update_notification",
                values,
                strict=True,
            )

            email_service = await get_email_service()
            try:
                await email_service.send_email(
                        to_email=payload["email"],
                        subject="Your password has been updated",
                        text=(
                        f"Hi {username},\n\n"
                        "Your password has been updated successfully.\n\n"
                        "If you did not request this, please ignore this email."
                    ),
                    html=html_content,
                )
                logger.info("Sent password update email to %s", payload["email"])
            except Exception as exc:
                logger.error(
                    "Failed to send password update emails for %s: %s",
                    payload["email"],
                    exc,
                    exc_info=True,
                )