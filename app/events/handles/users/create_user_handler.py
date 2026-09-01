import asyncio
import logging
from typing import Any
from app.deps.service import get_email_service, get_storage_service
from app.deps.service import get_email_template_service
from app.services.email_service import BrevoEmailService
from app.models.token_model import TokenType
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

BREVO_FIRST_NAME_ATTRIBUTE = "FIRSTNAME"
BREVO_LAST_NAME_ATTRIBUTE = "LASTNAME"


def split_full_name(full_name: str) -> tuple[str, str]:
    parts = [part for part in full_name.strip().split() if part]
    if not parts:
        return "User", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])

class CreateUserHandler:
    @staticmethod
    async def handle(payload: dict[str, Any]) -> None:
        user_id = payload["id"]
        email = payload["email"]
        public_id = str(payload["public_id"])

        token_manager = TokenManager()
        active_token = await token_manager.account_activation_token(public_id)


        if settings.FRONTEND_URL:
            active_link = settings.FRONTEND_URL.rstrip("/") + f"/activate-account/{active_token}"
        else:
            active_link = f"Use this verification token to activate your account: {active_token}"


        async with database.async_session() as session:
            token_service = TokenRepository(session)
            setting_service = SettingService(SettingRepository(session))
            
            tokens = await token_service.get_tokens(
                where_clause=(Token.user_id == user_id) &
                             (Token.type == TokenType.ACCOUNT_ACTIVATION)
            )
            if tokens:
                for token in tokens:
                    await token_service.delete_token(token)
            token_data = Token(
                user_id = user_id,
                token = active_token,
                expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS),
                type = TokenType.ACCOUNT_ACTIVATION
            )
            await token_service.create(token_data)

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
                "expires_in": settings.ACCOUNT_ACTIVATION_HOURS,
                "app_name": app_name,
                "year": current_year,
            }
            email_template_service = await get_email_template_service()
            html_content = await email_template_service.render_template(
                "activation_user_email",
                values,
                strict=True,
            )

            email_service = await get_email_service()
            try:
                await email_service.send_email(
                        to_email=email,
                        subject="Verify your email address",
                        text=(
                        f"Hi {username},\n\n"
                        "Please verify your email by clicking the link below:\n\n"
                        f"{active_link}\n\n"
                        "If you did not request this, please ignore this email."
                    ),
                    html=html_content,
                )
                logger.info("Sent registration email to %s", email)
            except Exception as exc:
                logger.error(
                    "Failed to send registration emails for %s: %s",
                    email,
                    exc,
                    exc_info=True,
                )

            # NOTE: Do NOT create mailing provider contact at registration.
            # Contact creation for newsletter/subscription will be performed
            # when the user activates their account to avoid creating
            # contacts for fake or undeliverable emails.
