import logging
from datetime import date
from typing import Any

from app.core.config import settings
from app.core.database import db as database
from app.deps.service import (
    get_email_service,
    get_email_template_service,
    get_storage_service,
)
from app.repositories.setting_repository import SettingRepository
from app.services.setting_service import SettingService

logger = logging.getLogger(__name__)


class AgreementInvitationSentHandler:
    @staticmethod
    async def handle(payload: dict[str, Any]) -> None:
        recipient_email = payload.get("recipient_email")
        if not recipient_email:
            logger.warning("AgreementInvitationSentHandler: Missing recipient_email in payload")
            return

        recipient_name = payload.get("recipient_name") or "Host Partner"
        token = payload.get("token") or ""
        commission_pct = payload.get("commission_percentage") or 10.0
        company_name = payload.get("company_name") or f"{recipient_name}'s Homestay"
        expires_in_days = payload.get("expires_in_days") or 7

        frontend_url = (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
        signing_url = f"{frontend_url}/agreements/{token}" if frontend_url else f"/agreements/{token}"
        current_year = date.today().year

        try:
            app_name = "TashiHome"
            tagline = "Authentic Homestays"
            logo_url = None
            legal_name = "TashiHome Technologies Pvt. Ltd."
            legal_address = "Gangtok, Sikkim, India"

            if database.async_session is not None:
                try:
                    async with database.async_session() as session:
                        setting_service = SettingService(SettingRepository(session))
                        storage_service = get_storage_service()

                        app_name_setting = await setting_service.get_by_key("app_name")
                        logo_setting = await setting_service.get_by_key("agreement_logo") or await setting_service.get_by_key("app_logo")
                        tagline_setting = await setting_service.get_by_key("app_tagline")
                        legal_name_setting = await setting_service.get_by_key("agreement_company_legal_name") or await setting_service.get_by_key("legal_name")
                        legal_address_setting = await setting_service.get_by_key("agreement_company_address") or await setting_service.get_by_key("contact_address")

                        if app_name_setting and app_name_setting.value:
                            app_name = app_name_setting.value
                        if tagline_setting and tagline_setting.value:
                            tagline = tagline_setting.value
                        if legal_name_setting and legal_name_setting.value:
                            legal_name = legal_name_setting.value
                        if legal_address_setting and legal_address_setting.value:
                            legal_address = legal_address_setting.value
                        if logo_setting and logo_setting.value:
                            logo_url = await storage_service.get_display_url(logo_setting.value)
                except Exception as db_err:
                    logger.warning("Could not read settings from db in agreement invitation handler: %s", db_err)

            template_data = {
                "app_name": app_name,
                "tagline": tagline,
                "logo_url": logo_url or "",
                "logo_display": "block" if logo_url else "none",
                "year": current_year,
                "host_name": recipient_name,
                "company_name": company_name,
                "commission_percentage": f"{float(commission_pct):.1f}",
                "expires_in_days": str(expires_in_days),
                "signing_url": signing_url,
                "legal_name": legal_name,
                "legal_address": legal_address,
                "support_email": getattr(settings, "SUPPORT_EMAIL", f"partner@{app_name.lower().replace(' ', '')}.in"),
            }

            email_template_service = await get_email_template_service()
            html_content = await email_template_service.render_template(
                "host_agreement_invitation",
                template_data,
                strict=False,
            )

            email_service = await get_email_service()
            await email_service.send_email(
                to_email=recipient_email,
                subject=f"Action Required: Execute Your {app_name} Host Partnership Agreement",
                text=(
                    f"Hello {recipient_name},\n\n"
                    f"Your host partnership agreement is ready for digital signature with an agreed platform commission rate of {commission_pct}%.\n\n"
                    f"Please review and electronically execute your agreement here:\n{signing_url}\n\n"
                    "Thank you,\n"
                    f"The {app_name} Team"
                ),
                html=html_content,
            )
            logger.info("Successfully dispatched agreement invitation email to %s via event handler", recipient_email)

        except Exception as exc:
            logger.error(
                "Failed to process agreement invitation email for %s: %s",
                recipient_email,
                exc,
                exc_info=True,
            )

