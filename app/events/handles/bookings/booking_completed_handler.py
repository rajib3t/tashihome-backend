import logging
from datetime import date as date_cls
from typing import Any

from app.core.database import db as database
from app.deps.service import get_email_service, get_email_template_service, get_storage_service
from app.repositories.booking_repository import BookingRepository
from app.repositories.setting_repository import SettingRepository
from app.repositories.tax_repository import TaxRepository
from app.services.invoice_service import InvoiceService
from app.services.setting_service import SettingService
from app.services.tax_service import TaxService

logger = logging.getLogger(__name__)


class BookingCompletedHandler:
    """Handles the booking.completed event: generates a PDF invoice and emails it to the guest."""

    @staticmethod
    async def handle(payload: dict[str, Any]) -> None:
        booking_id = payload.get("booking_id")

        async with database.async_session() as session:
            booking_repo = BookingRepository(session)
            setting_service = SettingService(SettingRepository(session))
            tax_service = TaxService(TaxRepository(session))
            storage_service = get_storage_service()

            # Safely fetch booking with all relations in this async session
            db_booking = None
            if booking_id:
                try:
                    db_booking = await booking_repo.get_by_id(
                        booking_id=booking_id,
                        with_relations={"guest": True, "property": True, "room_type": True},
                    )
                except Exception as exc:
                    logger.warning("Could not reload booking %s in handler: %s", booking_id, exc)

            guest = db_booking.guest if db_booking else None
            prop = db_booking.property if db_booking else None
            room_type = db_booking.room_type if db_booking else None

            guest_email = (
                guest.email
                if guest and guest.email
                else payload.get("guest_email")
            )
            if not guest_email:
                logger.warning(
                    "booking.completed: missing guest_email for booking %s, skipping email.",
                    payload.get("booking_reference"),
                )
                return

            guest_name = (
                guest.full_name
                if guest and guest.full_name
                else payload.get("guest_name") or "Guest"
            )
            guest_phone = (
                getattr(guest, "phone", None)
                if guest
                else payload.get("guest_phone")
            )
            booking_reference = (
                db_booking.booking_reference
                if db_booking
                else payload.get("booking_reference", "")
            )
            invoice_number = (
                db_booking.invoice_number
                if db_booking
                else payload.get("invoice_number", "")
            )
            property_name = (
                prop.name
                if prop
                else payload.get("property_name", "Homestay")
            )
            property_address = (
                prop.address
                if prop
                else payload.get("property_address")
            )
            room_type_name = (
                room_type.name
                if room_type
                else payload.get("room_type_name")
            )
            check_in_date = (
                str(db_booking.check_in_date)
                if db_booking
                else payload.get("check_in_date", "")
            )
            check_out_date = (
                str(db_booking.check_out_date)
                if db_booking
                else payload.get("check_out_date", "")
            )
            num_guests = (
                db_booking.num_guests
                if db_booking
                else payload.get("num_guests", 1)
            )
            num_rooms = (
                db_booking.num_rooms
                if db_booking
                else payload.get("num_rooms", 1)
            )
            price_per_night = (
                float(db_booking.price_per_night)
                if db_booking
                else float(payload.get("price_per_night", 0))
            )
            discount_amount = (
                float(db_booking.discount_amount or 0)
                if db_booking
                else float(payload.get("discount_amount", 0))
            )
            tax_amount = (
                float(db_booking.tax_amount or 0)
                if db_booking
                else float(payload.get("tax_amount", 0))
            )
            total_amount = (
                float(db_booking.total_amount)
                if db_booking
                else float(payload.get("total_amount", 0.0))
            )
            currency = (
                db_booking.currency
                if db_booking
                else payload.get("currency", "INR")
            )
            special_requests = (
                db_booking.special_requests
                if db_booking
                else payload.get("special_requests")
            )

            app_name_setting = await setting_service.get_by_key("app_name")
            logo_setting = await setting_service.get_by_key("app_logo")
            app_date_format = await setting_service.get_value(
                "app_date_format", "DD/MM/YYYY"
            )
            app_name = app_name_setting.value if app_name_setting else "Tashi Homes"
            logo_url = (
                await storage_service.get_display_url(logo_setting.value)
                if logo_setting and logo_setting.value
                else None
            )

            contact_email = await setting_service.get_value("contact_email", "")
            contact_phone = await setting_service.get_value("contact_phone", "")
            contact_address = await setting_service.get_value("contact_address", "")

            # Resolve default active tax
            default_tax = await tax_service.get_default_tax()
            gst_number = (
                default_tax.gst_number
                if default_tax and default_tax.gst_number
                else await setting_service.get_value("gst_number", "")
            )
            legal_name = (
                default_tax.legal_name
                if default_tax and default_tax.legal_name
                else await setting_service.get_value("legal_name", app_name)
            )
            tax_address = (
                default_tax.address
                if default_tax and default_tax.address
                else contact_address
            )
            hsn_sac_code = (
                default_tax.hsn_sac_code
                if default_tax and default_tax.hsn_sac_code
                else await setting_service.get_value("hsn_sac_code", "996311")
            )

            tax_rate = (
                float(default_tax.rate)
                if default_tax and default_tax.rate is not None
                else float(await setting_service.get_value("gst_percentage", "0") or 0)
            )
            cgst_rate = (
                float(default_tax.cgst_rate)
                if default_tax and default_tax.cgst_rate is not None
                else (tax_rate / 2.0 if tax_rate > 0 else None)
            )
            sgst_rate = (
                float(default_tax.sgst_rate)
                if default_tax and default_tax.sgst_rate is not None
                else (tax_rate / 2.0 if tax_rate > 0 else None)
            )
            igst_rate = (
                float(default_tax.igst_rate)
                if default_tax and default_tax.igst_rate is not None
                else None
            )
            is_tax_inclusive = (
                bool(default_tax.is_inclusive)
                if default_tax
                else (await setting_service.get_value("is_tax_inclusive", "false")).lower()
                == "true"
            )

            check_in_time = await setting_service.get_value("check_in_time", "14:00")
            check_out_time = await setting_service.get_value("check_out_time", "11:00")
            currency_symbol = await setting_service.get_value("currency_symbol", "₹")

        nights = 0
        try:
            ci = date_cls.fromisoformat(str(check_in_date))
            co = date_cls.fromisoformat(str(check_out_date))
            nights = (co - ci).days
        except Exception:
            nights = 0

        current_year = date_cls.today().year

        # ── 1. Generate PDF invoice ─────────────────────────────────────────
        pdf_data = {
            "booking_id": booking_id,
            "guest_id": payload.get("guest_id"),
            "guest_name": guest_name,
            "guest_email": guest_email,
            "guest_phone": guest_phone,
            "guest_gstin": payload.get("guest_gstin"),
            "booking_reference": booking_reference,
            "invoice_number": invoice_number,
            "property_name": property_name,
            "property_address": property_address,
            "room_type_name": room_type_name,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "num_guests": num_guests,
            "num_rooms": num_rooms,
            "price_per_night": price_per_night,
            "discount_amount": discount_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "currency": currency,
            "special_requests": special_requests,
            "app_name": app_name,
            "logo_url": logo_url,
            "app_date_format": app_date_format,
            "gst_number": gst_number,
            "legal_name": legal_name,
            "company_address": tax_address,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "hsn_sac_code": hsn_sac_code,
            "tax_rate": tax_rate,
            "cgst_rate": cgst_rate,
            "sgst_rate": sgst_rate,
            "igst_rate": igst_rate,
            "is_tax_inclusive": is_tax_inclusive,
            "check_in_time": check_in_time,
            "check_out_time": check_out_time,
            "currency_symbol": currency_symbol,
        }
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

        # ── 2. Format dates using platform setting ──────────────────────────
        from app.services.invoice_service import format_booking_date

        formatted_check_in = format_booking_date(check_in_date, app_date_format)
        formatted_check_out = format_booking_date(check_out_date, app_date_format)

        # ── 3. Render HTML email template ───────────────────────────────────
        template_values = {
            "logo_url": logo_url,
            "full_name": guest_name,
            "booking_reference": booking_reference,
            "invoice_number": invoice_number,
            "property_name": property_name,
            "check_in_date": formatted_check_in,
            "check_out_date": formatted_check_out,
            "nights": nights,
            "num_guests": num_guests,
            "num_rooms": num_rooms,
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

        # ── 4. Send email ───────────────────────────────────────────────────
        subject = f"Booking Confirmed — {property_name} [{booking_reference}]"
        text_body = (
            f"Hi {guest_name},\n\n"
            f"Your booking at {property_name} is confirmed!\n\n"
            f"Booking Reference : {booking_reference}\n"
            f"Invoice Number    : {invoice_number}\n"
            f"Check-in          : {formatted_check_in}\n"
            f"Check-out         : {formatted_check_out}\n"
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
