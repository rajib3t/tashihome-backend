"""Invoice PDF generation service using reportlab."""
import io
import logging
from datetime import datetime
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

logger = logging.getLogger(__name__)

# Brand colors
PRIMARY = colors.HexColor("#F4A020")   # Tashi Homes amber
DARK = colors.HexColor("#1A1A2E")      # Dark navy
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MID_GRAY = colors.HexColor("#888888")
WHITE = colors.white


class InvoiceService:
    """Generates a PDF invoice for a completed booking."""

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

        styles = getSampleStyleSheet()
        story = []

        # ---------- HEADER ----------
        header_data = [
            [
                Paragraph(
                    f"<font color='#F4A020'><b>{booking_data.get('app_name', 'Tashi Homes')}</b></font>",
                    ParagraphStyle(
                        "brand",
                        fontSize=20,
                        leading=24,
                        textColor=DARK,
                        fontName="Helvetica-Bold",
                    ),
                ),
                Paragraph(
                    "<b>INVOICE</b>",
                    ParagraphStyle(
                        "inv_label",
                        fontSize=26,
                        leading=30,
                        textColor=PRIMARY,
                        alignment=TA_RIGHT,
                        fontName="Helvetica-Bold",
                    ),
                ),
            ]
        ]
        header_table = Table(header_data, colWidths=[100 * mm, 80 * mm])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=8))

        # ---------- INVOICE META ----------
        issued_date = datetime.utcnow().strftime("%d %b %Y")
        meta_data = [
            ["Invoice No:", booking_data.get("invoice_number", "—"),
             "Issue Date:", issued_date],
            ["Booking Ref:", booking_data.get("booking_reference", "—"), "", ""],
        ]
        meta_style = ParagraphStyle("meta", fontSize=9, leading=13, fontName="Helvetica")
        meta_bold = ParagraphStyle("metabold", fontSize=9, leading=13, fontName="Helvetica-Bold")

        meta_rows = []
        for row in meta_data:
            meta_rows.append([
                Paragraph(row[0], meta_bold),
                Paragraph(str(row[1]), meta_style),
                Paragraph(row[2], meta_bold),
                Paragraph(str(row[3]), meta_style),
            ])

        meta_table = Table(meta_rows, colWidths=[30 * mm, 60 * mm, 30 * mm, 60 * mm])
        meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8 * mm))

        # ---------- BILLED TO ----------
        section_style = ParagraphStyle(
            "section", fontSize=9, leading=12,
            textColor=MID_GRAY, fontName="Helvetica",
        )
        value_style = ParagraphStyle(
            "value", fontSize=10, leading=14,
            fontName="Helvetica",
        )
        value_bold = ParagraphStyle(
            "valuebold", fontSize=10, leading=14,
            fontName="Helvetica-Bold",
        )

        billed_to = [
            [Paragraph("BILLED TO", section_style), Paragraph("PROPERTY", section_style)],
            [Paragraph(booking_data.get("guest_name", "Guest"), value_bold),
             Paragraph(booking_data.get("property_name", ""), value_bold)],
            [Paragraph(booking_data.get("guest_email", ""), value_style),
             Paragraph(booking_data.get("property_address", "") or "", value_style)],
        ]
        billed_table = Table(billed_to, colWidths=[90 * mm, 90 * mm])
        billed_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(billed_table)
        story.append(Spacer(1, 8 * mm))

        # ---------- LINE ITEMS ----------
        check_in = booking_data.get("check_in_date", "")
        check_out = booking_data.get("check_out_date", "")
        nights = 0
        try:
            from datetime import date as date_cls
            ci = date_cls.fromisoformat(str(check_in))
            co = date_cls.fromisoformat(str(check_out))
            nights = (co - ci).days
        except Exception:
            pass

        currency = booking_data.get("currency", "INR")
        price_per_night = booking_data.get("price_per_night", 0.0)
        num_rooms = booking_data.get("num_rooms", 1)
        discount = booking_data.get("discount_amount", 0.0)
        tax = booking_data.get("tax_amount", 0.0)
        total = booking_data.get("total_amount", 0.0)
        base_amount = price_per_night * num_rooms * nights

        col_header = ParagraphStyle(
            "col_header", fontSize=9, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER,
        )
        cell_left = ParagraphStyle("cell_left", fontSize=9, fontName="Helvetica", alignment=TA_LEFT)
        cell_right = ParagraphStyle("cell_right", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT)

        items_data = [
            # Header row
            [
                Paragraph("DESCRIPTION", col_header),
                Paragraph("CHECK-IN", col_header),
                Paragraph("CHECK-OUT", col_header),
                Paragraph("NIGHTS", col_header),
                Paragraph("ROOMS", col_header),
                Paragraph(f"AMOUNT ({currency})", col_header),
            ],
            # Data row
            [
                Paragraph(f"Room stay - {booking_data.get('property_name', '')}", cell_left),
                Paragraph(str(check_in), cell_left),
                Paragraph(str(check_out), cell_left),
                Paragraph(str(nights), cell_left),
                Paragraph(str(num_rooms), cell_left),
                Paragraph(f"{base_amount:,.2f}", cell_right),
            ],
        ]

        items_table = Table(
            items_data,
            colWidths=[60 * mm, 22 * mm, 22 * mm, 15 * mm, 15 * mm, 26 * mm],
        )
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 6 * mm))

        # ---------- TOTALS ----------
        totals_right = ParagraphStyle("tot_r", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT)
        totals_right_bold = ParagraphStyle("tot_rb", fontSize=10, fontName="Helvetica-Bold", alignment=TA_RIGHT)

        totals_data = [
            ["", Paragraph("Subtotal:", totals_right), Paragraph(f"{currency} {base_amount:,.2f}", totals_right)],
        ]
        if discount > 0:
            totals_data.append(
                ["", Paragraph("Discount:", totals_right), Paragraph(f"- {currency} {discount:,.2f}", totals_right)]
            )
        if tax > 0:
            totals_data.append(
                ["", Paragraph("Tax:", totals_right), Paragraph(f"+ {currency} {tax:,.2f}", totals_right)]
            )
        totals_data.append(
            ["", Paragraph("<b>Total:</b>", totals_right_bold), Paragraph(f"<b>{currency} {total:,.2f}</b>", totals_right_bold)]
        )

        totals_table = Table(totals_data, colWidths=[90 * mm, 50 * mm, 40 * mm])
        totals_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (1, -1), (-1, -1), 1.5, DARK),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 10 * mm))
        story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        story.append(Spacer(1, 4 * mm))

        # ---------- FOOTER ----------
        footer_style = ParagraphStyle(
            "footer", fontSize=8, leading=12,
            textColor=MID_GRAY, alignment=TA_CENTER,
        )
        story.append(Paragraph(
            f"Thank you for your booking! — {booking_data.get('app_name', 'Tashi Homes')} — "
            f"This is a computer-generated invoice and does not require a signature.",
            footer_style,
        ))

        doc.build(story)
        return buffer.getvalue()
