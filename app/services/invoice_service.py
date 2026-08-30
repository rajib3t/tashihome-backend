"""Invoice PDF generation service using reportlab."""
import io
import logging
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

# ── Brand palette ────────────────────────────────────────────────────────────
PRIMARY    = colors.HexColor("#F4A020")   # amber
DARK       = colors.HexColor("#0C4550")   # deep teal / navy
LIGHT_GRAY = colors.HexColor("#F5F7F8")
MID_GRAY   = colors.HexColor("#888888")
WHITE      = colors.white

# Usable page width: A4 (210mm) − 15mm left − 15mm right = 180mm
PAGE_W = 180 * mm


def _format_booking_date(value: Any, date_format: str) -> str:
    """Format an ISO booking date using the app's Moment-style date setting."""
    if not value:
        return ""

    try:
        booking_date = datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        return str(value)

    format_map = {
        "YYYY": "%Y",
        "YY": "%y",
        "MMMM": "%B",
        "MMM": "%b",
        "MM": "%m",
        "DD": "%d",
    }
    python_format = date_format or "DD/MM/YYYY"
    for token in ("YYYY", "YY", "MMMM", "MMM", "MM", "DD"):
        python_format = python_format.replace(token, format_map[token])

    try:
        return booking_date.strftime(python_format)
    except ValueError:
        logger.warning("Invalid app date format %r; using DD/MM/YYYY.", date_format)
        return booking_date.strftime("%d/%m/%Y")


def _fetch_logo(url: Optional[str], max_height: float = 14 * mm) -> Optional[Image]:
    """Download a logo image from a URL and return a scaled ReportLab Image, or None."""
    if not url:
        return None
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read()
        img = Image(io.BytesIO(data))
        # Scale proportionally so height == max_height
        ratio = img.imageWidth / img.imageHeight
        img.drawHeight = max_height
        img.drawWidth = max_height * ratio
        return img
    except Exception as exc:
        logger.warning("Could not fetch logo from %s: %s", url, exc)
        return None


class InvoiceService:
    """Generates a professional A4 PDF invoice for a completed booking."""

    def generate_pdf(self, booking_data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF invoice from booking data dict.
        Returns raw PDF bytes ready to be attached to an email.
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        story: list = []
        app_name = booking_data.get("app_name", "Tashi Homes")

        # ── 1. HEADER: logo + "INVOICE" label ───────────────────────────────
        logo_img = _fetch_logo(booking_data.get("logo_url"))

        if logo_img:
            left_cell = logo_img
        else:
            left_cell = Paragraph(
                f"<font color='#F4A020'><b>{app_name}</b></font>",
                ParagraphStyle(
                    "brand", fontSize=22, leading=26,
                    textColor=DARK, fontName="Helvetica-Bold",
                ),
            )

        right_cell = Paragraph(
            "<b>INVOICE</b>",
            ParagraphStyle(
                "inv_label", fontSize=26, leading=30,
                textColor=PRIMARY, alignment=TA_RIGHT,
                fontName="Helvetica-Bold",
            ),
        )

        header_table = Table(
            [[left_cell, right_cell]],
            colWidths=[PAGE_W * 0.55, PAGE_W * 0.45],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)

        # App name under logo (only when logo is shown)
        if logo_img:
            story.append(Spacer(1, 1 * mm))
            story.append(Paragraph(
                f"<b>{app_name}</b>",
                ParagraphStyle(
                    "brand_sub", fontSize=9, leading=11,
                    textColor=DARK, fontName="Helvetica",
                ),
            ))

        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=6 * mm))

        # ── 2. INVOICE META (ref + date) ─────────────────────────────────────
        issued_date = datetime.utcnow().strftime("%d %b %Y")
        meta_bold  = ParagraphStyle("mb",  fontSize=9, leading=13, fontName="Helvetica-Bold")
        meta_style = ParagraphStyle("ms",  fontSize=9, leading=13, fontName="Helvetica")

        meta_rows = [
            [
                Paragraph("Invoice No:",    meta_bold),
                Paragraph(booking_data.get("invoice_number", "—"), meta_style),
                Paragraph("Issue Date:",    meta_bold),
                Paragraph(issued_date,      meta_style),
            ],
            [
                Paragraph("Booking Ref:",   meta_bold),
                Paragraph(booking_data.get("booking_reference", "—"), meta_style),
                Paragraph("", meta_style),
                Paragraph("", meta_style),
            ],
        ]
        meta_table = Table(meta_rows, colWidths=[28*mm, 62*mm, 28*mm, 62*mm])
        meta_table.setStyle(TableStyle([
            ("VALIGN",         (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",     (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 3),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 7 * mm))

        # ── 3. BILLED TO / PROPERTY ──────────────────────────────────────────
        sec_style  = ParagraphStyle("sec", fontSize=8, leading=11,
                                    textColor=MID_GRAY, fontName="Helvetica")
        val_bold   = ParagraphStyle("vb",  fontSize=10, leading=14, fontName="Helvetica-Bold")
        val_style  = ParagraphStyle("vs",  fontSize=9,  leading=13, fontName="Helvetica")

        billed_table = Table(
            [
                [Paragraph("BILLED TO", sec_style),   Paragraph("PROPERTY", sec_style)],
                [Paragraph(booking_data.get("guest_name", "Guest"), val_bold),
                 Paragraph(booking_data.get("property_name", ""), val_bold)],
                [Paragraph(booking_data.get("guest_email", "") or "", val_style),
                 Paragraph(booking_data.get("property_address", "") or "", val_style)],
            ],
            colWidths=[PAGE_W / 2, PAGE_W / 2],
        )
        billed_table.setStyle(TableStyle([
            ("VALIGN",         (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",     (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 3),
            ("LEFTPADDING",    (0, 0), (-1, -1), 7),
            ("BACKGROUND",     (0, 0), (-1,  0), LIGHT_GRAY),
            ("TOPPADDING",     (0, 0), (-1,  0), 6),
            ("BOTTOMPADDING",  (0, 0), (-1,  0), 6),
        ]))
        story.append(billed_table)
        story.append(Spacer(1, 7 * mm))

        # ── 4. LINE ITEMS TABLE ──────────────────────────────────────────────
        check_in  = booking_data.get("check_in_date", "")
        check_out = booking_data.get("check_out_date", "")
        date_format = booking_data.get("app_date_format", "DD/MM/YYYY")
        formatted_check_in = _format_booking_date(check_in, date_format)
        formatted_check_out = _format_booking_date(check_out, date_format)
        nights    = 0
        try:
            from datetime import date as date_cls
            nights = (date_cls.fromisoformat(str(check_out)) -
                      date_cls.fromisoformat(str(check_in))).days
        except Exception:
            pass

        currency       = booking_data.get("currency", "INR")
        price_per_night = float(booking_data.get("price_per_night", 0))
        num_rooms      = int(booking_data.get("num_rooms", 1))
        num_guests     = int(booking_data.get("num_guests", 1))
        discount       = float(booking_data.get("discount_amount", 0))
        tax            = float(booking_data.get("tax_amount", 0))
        total          = float(booking_data.get("total_amount", 0))
        base_amount    = price_per_night * num_rooms * nights

        col_hdr  = ParagraphStyle("ch",  fontSize=8, fontName="Helvetica-Bold",
                                  textColor=WHITE, alignment=TA_CENTER, leading=11)
        cell_l   = ParagraphStyle("cl",  fontSize=9, fontName="Helvetica",
                                  alignment=TA_LEFT,  leading=12)
        cell_c   = ParagraphStyle("cc",  fontSize=9, fontName="Helvetica",
                                  alignment=TA_CENTER, leading=12)
        cell_r   = ParagraphStyle("cr",  fontSize=9, fontName="Helvetica",
                                  alignment=TA_RIGHT,  leading=12)

        # Column widths — total = 180mm
        # Desc=62, Check-in=26, Check-out=26, Nights=18, Rooms=18, Amount=30
        col_w = [62*mm, 26*mm, 26*mm, 18*mm, 18*mm, 30*mm]

        items_data = [
            [
                Paragraph("DESCRIPTION",        col_hdr),
                Paragraph("CHECK-IN",           col_hdr),
                Paragraph("CHECK-OUT",          col_hdr),
                Paragraph("NIGHTS",             col_hdr),
                Paragraph("ROOMS",              col_hdr),
                Paragraph(f"AMOUNT ({currency})", col_hdr),
            ],
            [
                Paragraph(f"Room stay — {booking_data.get('property_name', '')}", cell_l),
                Paragraph(formatted_check_in,   cell_c),
                Paragraph(formatted_check_out,  cell_c),
                Paragraph(str(nights),          cell_c),
                Paragraph(str(num_rooms),       cell_c),
                Paragraph(f"{base_amount:,.2f}", cell_r),
            ],
        ]

        items_table = Table(items_data, colWidths=col_w)
        items_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1,  0), DARK),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            # Amber accent on first data column
            ("TEXTCOLOR",     (0, 1), (0, -1),  PRIMARY),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 5 * mm))

        # ── 5. TOTALS ────────────────────────────────────────────────────────
        tot_r  = ParagraphStyle("tr",  fontSize=9,  fontName="Helvetica",      alignment=TA_RIGHT)
        tot_rb = ParagraphStyle("trb", fontSize=10, fontName="Helvetica-Bold", alignment=TA_RIGHT)

        totals_data = [
            ["", Paragraph("Subtotal:", tot_r),
                 Paragraph(f"{currency} {base_amount:,.2f}", tot_r)],
        ]
        if discount > 0:
            totals_data.append(
                ["", Paragraph("Discount:", tot_r),
                     Paragraph(f"− {currency} {discount:,.2f}", tot_r)]
            )
        if tax > 0:
            totals_data.append(
                ["", Paragraph("Tax:", tot_r),
                     Paragraph(f"+ {currency} {tax:,.2f}", tot_r)]
            )
        totals_data.append(
            ["", Paragraph("<b>Total:</b>", tot_rb),
                 Paragraph(f"<b>{currency} {total:,.2f}</b>", tot_rb)]
        )

        totals_table = Table(totals_data, colWidths=[95*mm, 45*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE",     (1, -1), (-1, -1), 1.5, DARK),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 10 * mm))

        # ── 6. FOOTER ────────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY, spaceAfter=4 * mm))
        story.append(Paragraph(
            f"Thank you for choosing <b>{app_name}</b>!  "
            "This is a computer-generated invoice and does not require a signature.",
            ParagraphStyle("footer", fontSize=8, leading=12,
                           textColor=MID_GRAY, alignment=TA_CENTER),
        ))

        doc.build(story)
        return buffer.getvalue()
