import logging
from datetime import date as date_cls
from typing import Any

from app.core.database import db as database
from app.deps.service import get_email_service, get_email_template_service, get_storage_service
from app.repositories.setting_repository import SettingRepository
from app.services.invoice_service import InvoiceService
from app.services.setting_service import SettingService

logger = logging.getLogger(__name__)


class BookingCompletedHandler:
    """Handles the booking.completed event: generates a PDF invoice and emails it to the guest."""

    @staticmethod
    async def handle(payload: dict[str, Any]) -> None:
        guest_email = payload.get("guest_email")
        if not guest_email:
            logger.warning(
                "booking.completed: missing guest_email for booking %s, skipping email.",
                payload.get("booking_reference"),
            )
            return

        guest_name = payload.get("guest_name") or "Guest"
        booking_reference = payload.get("booking_reference", "")
        invoice_number = payload.get("invoice_number", "")
        property_name = payload.get("property_name", "")
        check_in_date = payload.get("check_in_date", "")
        check_out_date = payload.get("check_out_date", "")
        total_amount = payload.get("total_amount", 0.0)
        currency = payload.get("currency", "INR")

        try:
            nights = 0
            ci = date_cls.fromisoformat(str(check_in_date))
            co = date_cls.fromisoformat(str(check_out_date))
            nights = (co - ci).days
        except Exception:
            nights = 0

        async with database.async_session() as session:
            setting_service = SettingService(SettingRepository(session))
            storage_service = get_storage_service()

            app_name_setting = await setting_service.get_by_key("app_name")
            logo_setting = await setting_service.get_by_key("app_logo")
            app_name = app_name_setting.value if app_name_setting else "Tashi Homes"
            logo_url = (
                await storage_service.get_display_url(logo_setting.value)
                if logo_setting and logo_setting.value
                else None
            )

        current_year = date_cls.today().year

        # ── 1. Generate PDF invoice ─────────────────────────────────────────
        pdf_data = {**payload, "app_name": app_name}
        invoice_bytes: bytes = b""
        try:
            invoice_service = InvoiceService()
            invoice_bytes = invoice_service.generate_pdf(pdf_data)
            logger.info(
                "Generated PDF invoice for booking %s (%s bytes).",
                booking_reference,
                len(invoice_bytes),
            )
        except Exception as exc:
            logger.error(
                "Failed to generate PDF for booking %s: %s",
                booking_reference,
                exc,
                exc_info=True,
            )
            # Continue to send email without PDF attachment if generation fails

        # ── 2. Render HTML email template ───────────────────────────────────
        template_values = {
            "logo_url": logo_url,
            "full_name": guest_name,
            "booking_reference": booking_reference,
            "invoice_number": invoice_number,
            "property_name": property_name,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "nights": nights,
            "num_guests": payload.get("num_guests", 1),
            "num_rooms": payload.get("num_rooms", 1),
            "total_amount": f"{total_amount:,.2f}",
            "currency": currency,
            "app_name": app_name,
            "year": current_year,
        }

        html_content: str | None = None
        try:
            email_template_service = await get_email_template_service()
            html_content = await email_template_service.render_template(
                "order_confirmation_email",
                template_values,
                strict=False,
            )
        except Exception as exc:
            logger.warning(
                "Could not render HTML email template for booking %s: %s",
                booking_reference,
                exc,
            )

        # ── 3. Send email ───────────────────────────────────────────────────
        subject = f"Booking Confirmed — {property_name} [{booking_reference}]"
        text_body = (
            f"Hi {guest_name},\n\n"
            f"Your booking at {property_name} is confirmed!\n\n"
            f"Booking Reference : {booking_reference}\n"
            f"Invoice Number    : {invoice_number}\n"
            f"Check-in          : {check_in_date}\n"
            f"Check-out         : {check_out_date}\n"
            f"Total Amount      : {currency} {total_amount:,.2f}\n\n"
            "Please find your invoice attached to this email.\n\n"
            f"Thank you for choosing {app_name}!"
        )

        attachments = []
        if invoice_bytes:
            from app.services.email_service import EmailAttachment
            attachments.append(
                EmailAttachment(
                    filename=f"invoice_{invoice_number}.pdf",
                    content=invoice_bytes,
                    mimetype="application/pdf",
                )
            )

        try:
            email_service = await get_email_service()
            await email_service.send_email(
                to_email=guest_email,
                subject=subject,
                text=text_body,
                html=html_content,
                attachments=attachments if attachments else None,
            )
            logger.info(
                "Sent order confirmation email to %s for booking %s.",
                guest_email,
                booking_reference,
            )
        except Exception as exc:
            logger.error(
                "Failed to send order confirmation email to %s for booking %s: %s",
                guest_email,
                booking_reference,
                exc,
                exc_info=True,
            )
