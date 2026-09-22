import base64
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
from app.services.email_service import EmailAttachment
from app.services.setting_service import SettingService

logger = logging.getLogger(__name__)


class AgreementCompletedHandler:
    @staticmethod
    async def handle(payload: dict[str, Any]) -> None:
        signer_email = payload.get("signer_email")
        if not signer_email:
            logger.warning("AgreementCompletedHandler: Missing signer_email in payload")
            return

        signer_name = payload.get("signer_name") or "Host Partner"
        company_name = payload.get("company_name") or f"{signer_name}'s Homestay"
        token = payload.get("token") or ""
        public_id = payload.get("public_id") or ""
        signed_at_str = payload.get("signed_at") or ""
        pdf_file_url = payload.get("pdf_file_url")
        pdf_bytes_b64 = payload.get("pdf_bytes_b64")

        frontend_url = (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
        agreement_view_url = f"{frontend_url}/vendor/agreements" if frontend_url else "/vendor/agreements"
        dashboard_url = f"{frontend_url}/vendor" if frontend_url else "/vendor"
        current_year = date.today().year

        try:
            app_name = "TashiHome"
            tagline = "Authentic Homestays"
            logo_url = None
            legal_name = "TashiHome Technologies Pvt. Ltd."
            legal_address = "Gangtok, Sikkim, India"
            storage_service = get_storage_service()

            if database.async_session is not None:
                try:
                    async with database.async_session() as session:
                        setting_service = SettingService(SettingRepository(session))

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
                    logger.warning("Could not read settings from db in agreement completed handler: %s", db_err)

            template_data = {
                "app_name": app_name,
                "tagline": tagline,
                "logo_url": logo_url or "",
                "logo_display": "block" if logo_url else "none",
                "year": current_year,
                "host_name": signer_name,
                "company_name": company_name,
                "legal_name": legal_name,
                "legal_address": legal_address,
                "agreement_ref": f"AGMT-{str(public_id)[:8].upper()}" if public_id else "AGMT-EXECUTED",
                "signed_date": signed_at_str,
                "agreement_view_url": agreement_view_url,
                "pdf_download_url": agreement_view_url,
                "dashboard_url": dashboard_url,
                "support_email": getattr(settings, "SUPPORT_EMAIL", f"partner@{app_name.lower().replace(' ', '')}.in"),
            }


            email_template_service = await get_email_template_service()
            html_content = await email_template_service.render_template(
                "host_agreement_completed",
                template_data,
                strict=False,
            )

            # Prepare PDF attachment if available
            attachments: list[EmailAttachment] = []
            pdf_bytes: bytes | None = None
            if pdf_bytes_b64:
                try:
                    pdf_bytes = base64.b64decode(pdf_bytes_b64)
                except Exception as b64_err:
                    logger.warning("Could not decode pdf_bytes_b64 in completed agreement event: %s", b64_err)

            if not pdf_bytes and pdf_file_url:
                try:
                    pdf_bytes = await storage_service.download_bytes(pdf_file_url)
                except Exception as dl_err:
                    logger.warning("Could not fetch agreement PDF from storage %s: %s", pdf_file_url, dl_err)

            if pdf_bytes:
                attachments.append(
                    EmailAttachment(
                        filename=f"{app_name.replace(' ', '_')}_Host_Agreement_{public_id[:8]}.pdf",
                        content=pdf_bytes,
                        mimetype="application/pdf",
                    )
                )

            email_service = await get_email_service()
            await email_service.send_email(
                to_email=signer_email,
                subject=f"Executed Copy: Your {app_name} Host Partnership Agreement",
                text=(
                    f"Hello {signer_name},\n\n"
                    f"Your partnership agreement with {app_name} has been successfully executed with bilateral digital signatures.\n\n"
                    f"You can view your executed agreement and digital certificate here:\n{agreement_view_url}\n\n"
                    "Thank you,\n"
                    f"The {app_name} Team"
                ),
                html=html_content,
                attachments=attachments if attachments else None,
            )
            logger.info("Successfully dispatched executed agreement email to %s via event handler", signer_email)

        except Exception as exc:
            logger.error(
                "Failed to process executed agreement email for %s: %s",
                signer_email,
                exc,
                exc_info=True,
            )
