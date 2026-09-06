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
PRIMARY         = colors.HexColor("#D97706")   # Amber / Gold accent
PRIMARY_DARK    = colors.HexColor("#B45309")
PRIMARY_LIGHT   = colors.HexColor("#FEF3C7")   # Soft amber tint
DARK            = colors.HexColor("#0F2937")   # Deep navy / charcoal
DARK_HEADER     = colors.HexColor("#1E293B")   # Slate 800
LIGHT_BG        = colors.HexColor("#F8FAFC")   # Slate 50
CARD_BORDER     = colors.HexColor("#E2E8F0")   # Slate 200
LINE_BORDER     = colors.HexColor("#CBD5E1")   # Slate 300
TEXT_DARK       = colors.HexColor("#0F172A")   # Slate 900
TEXT_MUTED      = colors.HexColor("#64748B")   # Slate 500
GREEN_PAID      = colors.HexColor("#16A34A")   # Emerald 600
GREEN_BG        = colors.HexColor("#DCFCE7")   # Emerald 100
WHITE           = colors.white

# Usable page width: A4 (210mm) − 12mm left − 12mm right = 186mm
PAGE_W = 186 * mm


def format_booking_date(value: Any, date_format: str = "DD/MM/YYYY") -> str:
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


# Backward compatibility alias
_format_booking_date = format_booking_date


def _amount_to_words(amount: float, currency: str = "INR") -> str:
    """Convert numerical amount into Indian currency words representation."""
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
             "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _convert_below_thousand(n: int) -> str:
        words = []
        if n >= 100:
            words.append(units[n // 100] + " Hundred")
            n %= 100
        if n >= 20:
            words.append(tens[n // 10])
            n %= 10
        if n > 0:
            words.append(units[n])
        return " ".join(words)

    val = int(round(amount))
    if val == 0:
        return "Zero Rupees Only"

    parts = []
    crores = val // 10000000
    if crores > 0:
        parts.append(_convert_below_thousand(crores) + " Crore")
        val %= 10000000

    lakhs = val // 100000
    if lakhs > 0:
        parts.append(_convert_below_thousand(lakhs) + " Lakh")
        val %= 100000

    thousands = val // 1000
    if thousands > 0:
        parts.append(_convert_below_thousand(thousands) + " Thousand")
        val %= 1000

    if val > 0:
        parts.append(_convert_below_thousand(val))

    currency_label = "Rupees" if currency.upper() in ("INR", "RS", "₹") else currency.upper()
    return " ".join(parts).strip() + f" {currency_label} Only"


def _fetch_logo(url: Optional[str], max_height: float = 14 * mm) -> Optional[Image]:
    """Download a logo image from a URL and return a scaled ReportLab Image, or None."""
    if not url:
        return None
    try:
        with urllib.request.urlopen(url, timeout=4) as resp:
            data = resp.read()
        img = Image(io.BytesIO(data))
        ratio = img.imageWidth / img.imageHeight
        img.drawHeight = max_height
        img.drawWidth = max_height * ratio
        return img
    except Exception as exc:
        logger.warning("Could not fetch logo from %s: %s", url, exc)
        return None


class InvoiceService:
    """Generates a professional, detailed A4 PDF tax invoice with full GST details for a booking."""

    def generate_pdf(self, booking_data: Dict[str, Any]) -> bytes:
        """
        Generate a comprehensive PDF invoice from booking data dict.
        Returns raw PDF bytes ready to be attached to an email.
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=12 * mm,
            leftMargin=12 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )

        story: list = []

        # ── 0. Extract Parameters & Settings ────────────────────────────────
        app_name = booking_data.get("app_name") or "Tashi Homes"
        legal_name = booking_data.get("legal_name") or app_name
        gst_number = booking_data.get("gst_number") or ""
        company_address = booking_data.get("company_address") or ""
        contact_email = booking_data.get("contact_email") or ""
        contact_phone = booking_data.get("contact_phone") or ""
        hsn_sac_code = booking_data.get("hsn_sac_code") or "996311"

        date_format = booking_data.get("app_date_format", "DD/MM/YYYY")
        currency = booking_data.get("currency", "INR")

        check_in_raw = booking_data.get("check_in_date", "")
        check_out_raw = booking_data.get("check_out_date", "")
        formatted_check_in = format_booking_date(check_in_raw, date_format)
        formatted_check_out = format_booking_date(check_out_raw, date_format)
        formatted_issue_date = format_booking_date(datetime.utcnow().date(), date_format)

        check_in_time = booking_data.get("check_in_time", "14:00")
        check_out_time = booking_data.get("check_out_time", "11:00")

        nights = 0
        try:
            from datetime import date as date_cls
            nights = (date_cls.fromisoformat(str(check_out_raw)) -
                      date_cls.fromisoformat(str(check_in_raw))).days
        except Exception:
            nights = 0
        nights = max(1, nights)

        price_per_night = float(booking_data.get("price_per_night", 0))
        num_rooms = int(booking_data.get("num_rooms", 1))
        num_guests = int(booking_data.get("num_guests", 1))
        discount_amount = float(booking_data.get("discount_amount", 0))
        tax_amount = float(booking_data.get("tax_amount", 0))
        total_amount = float(booking_data.get("total_amount", 0))
        base_amount = round(price_per_night * num_rooms * nights, 2)

        tax_rate = float(booking_data.get("tax_rate") or 0)
        cgst_rate = booking_data.get("cgst_rate")
        sgst_rate = booking_data.get("sgst_rate")
        igst_rate = booking_data.get("igst_rate")
        is_tax_inclusive = bool(booking_data.get("is_tax_inclusive", False))

        is_tax_invoice = bool(gst_number or tax_amount > 0)

        # Calculate taxable value
        if is_tax_inclusive and tax_amount > 0:
            taxable_value = round(base_amount - discount_amount - tax_amount, 2)
        else:
            taxable_value = round(base_amount - discount_amount, 2)

        # ── 1. HEADER: BRAND & PROVIDER INFO (Left) vs TAX INVOICE BADGE & META (Right) ──
        logo_img = _fetch_logo(booking_data.get("logo_url"), max_height=12 * mm)

        company_html_lines = []
        company_html_lines.append(f"<font size=10 color='#0F2937'><b>{legal_name}</b></font>")
        if company_address:
            company_html_lines.append(f"<font size=7.5 color='#64748B'>{company_address}</font>")
        contact_line = []
        if contact_email:
            contact_line.append(f"Email: {contact_email}")
        if contact_phone:
            contact_line.append(f"Tel: {contact_phone}")
        if contact_line:
            company_html_lines.append(f"<font size=7.5 color='#64748B'>{' | '.join(contact_line)}</font>")
        if gst_number:
            company_html_lines.append(
                f"<font size=8 color='#0F2937'><b>GSTIN / Tax ID:</b> <font color='#D97706'><b>{gst_number}</b></font></font>"
            )

        left_header_elements = []
        if logo_img:
            left_header_elements.append(logo_img)
            left_header_elements.append(Spacer(1, 1.5 * mm))
        left_header_elements.append(
            Paragraph(
                "<br/>".join(company_html_lines),
                ParagraphStyle("company_block", leading=11),
            )
        )

        inv_title = "TAX INVOICE" if is_tax_invoice else "INVOICE"
        right_header_lines = [
            f"<font size=18 color='#D97706'><b>{inv_title}</b></font>  <font size=9 color='#16A34A'><b>[✓ PAID]</b></font>",
            "<br/>",
            f"<font size=8 color='#0F2937'><b>Invoice No:</b> {booking_data.get('invoice_number', '—')}</font>",
            f"<font size=8 color='#0F2937'><b>Issue Date:</b> {formatted_issue_date}</font>",
            f"<font size=8 color='#0F2937'><b>Booking Ref:</b> {booking_data.get('booking_reference', '—')}</font>",
            f"<font size=8 color='#0F2937'><b>SAC / HSN:</b> {hsn_sac_code} (Accommodation)</font>",
        ]

        right_header_block = Paragraph(
            "<br/>".join(right_header_lines),
            ParagraphStyle("inv_meta_right", leading=12, alignment=TA_RIGHT),
        )

        header_table = Table(
            [[left_header_elements, right_header_block]],
            colWidths=[PAGE_W * 0.55, PAGE_W * 0.45],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 2 * mm))
        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=3 * mm))

        # ── 2. TWO-COLUMN CARDS: BILLED TO (Guest) & RESERVATION DETAILS (Property) ──
        card_hdr_l = ParagraphStyle("chl", fontSize=7.5, fontName="Helvetica-Bold", textColor=WHITE, leading=9)
        card_txt_b = ParagraphStyle("ctb", fontSize=9, fontName="Helvetica-Bold", textColor=DARK, leading=12)
        card_txt_m = ParagraphStyle("ctm", fontSize=8, fontName="Helvetica", textColor=TEXT_MUTED, leading=11)
        card_txt_d = ParagraphStyle("ctd", fontSize=8, fontName="Helvetica", textColor=DARK, leading=11)

        guest_name = booking_data.get("guest_name", "Guest")
        guest_email = booking_data.get("guest_email", "")
        guest_phone = booking_data.get("guest_phone", "")
        guest_gstin = booking_data.get("guest_gstin", "")

        guest_lines = [
            Paragraph(f"<b>{guest_name}</b>", card_txt_b),
        ]
        if guest_email:
            guest_lines.append(Paragraph(f"Email: {guest_email}", card_txt_m))
        if guest_phone:
            guest_lines.append(Paragraph(f"Phone: {guest_phone}", card_txt_m))
        if guest_gstin:
            guest_lines.append(Paragraph(f"<b>Guest GSTIN:</b> {guest_gstin}", card_txt_d))
        else:
            guest_lines.append(Paragraph("Category: Retail / Individual Guest", card_txt_m))

        prop_name = booking_data.get("property_name", "Homestay")
        prop_addr = booking_data.get("property_address", "")
        room_name = booking_data.get("room_type_name") or "Standard Room"

        stay_lines = [
            Paragraph(f"<b>{prop_name}</b>", card_txt_b),
        ]
        if prop_addr:
            stay_lines.append(Paragraph(prop_addr, card_txt_m))
        stay_lines.append(
            Paragraph(
                f"Room: <b>{room_name}</b>  ({num_rooms} Room{'s' if num_rooms > 1 else ''}, {num_guests} Guest{'s' if num_guests > 1 else ''})",
                card_txt_d,
            )
        )
        stay_lines.append(
            Paragraph(
                f"Check-in: <b>{formatted_check_in}</b> (from {check_in_time}) • Check-out: <b>{formatted_check_out}</b> (until {check_out_time})",
                card_txt_m,
            )
        )

        card_col_w = (PAGE_W - 4 * mm) / 2
        cards_table = Table(
            [
                [
                    Paragraph("<b>BILLED TO (CUSTOMER / GUEST)</b>", card_hdr_l),
                    Paragraph("<b>HOMESTAY & STAY DETAILS</b>", card_hdr_l),
                ],
                [guest_lines, stay_lines],
            ],
            colWidths=[card_col_w, card_col_w],
        )
        cards_table.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (0, 0), DARK_HEADER),
            ("BACKGROUND",     (1, 0), (1, 0), DARK),
            ("BACKGROUND",     (0, 1), (-1, 1), LIGHT_BG),
            ("GRID",           (0, 0), (-1, -1), 0.5, CARD_BORDER),
            ("VALIGN",         (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",     (0, 0), (-1, 0), 3),
            ("BOTTOMPADDING",  (0, 0), (-1, 0), 3),
            ("LEFTPADDING",    (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 5),
            ("TOPPADDING",     (0, 1), (-1, 1), 4),
            ("BOTTOMPADDING",  (0, 1), (-1, 1), 5),
        ]))
        story.append(cards_table)
        story.append(Spacer(1, 4 * mm))

        # ── 3. ITEMIZED STAY CHARGES TABLE ──────────────────────────────────
        tbl_hdr = ParagraphStyle("th", fontSize=7.5, fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_CENTER, leading=9)
        tbl_cell_l = ParagraphStyle("tcl", fontSize=8, fontName="Helvetica", textColor=DARK, alignment=TA_LEFT, leading=10.5)
        tbl_cell_c = ParagraphStyle("tcc", fontSize=8, fontName="Helvetica", textColor=DARK, alignment=TA_CENTER, leading=10.5)
        tbl_cell_r = ParagraphStyle("tcr", fontSize=8, fontName="Helvetica", textColor=DARK, alignment=TA_RIGHT, leading=10.5)
        tbl_cell_b = ParagraphStyle("tcb", fontSize=8, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT, leading=10.5)

        col_widths = [8*mm, 56*mm, 40*mm, 14*mm, 14*mm, 24*mm, 30*mm]

        items_table_data = [
            [
                Paragraph("#", tbl_hdr),
                Paragraph("DESCRIPTION & SAC", tbl_hdr),
                Paragraph("STAY PERIOD", tbl_hdr),
                Paragraph("NIGHTS", tbl_hdr),
                Paragraph("ROOMS", tbl_hdr),
                Paragraph(f"RATE / NIGHT ({currency})", tbl_hdr),
                Paragraph(f"TAXABLE AMT ({currency})", tbl_hdr),
            ],
            [
                Paragraph("1", tbl_cell_c),
                Paragraph(
                    f"<b>Homestay Accommodation</b><br/><font color='#64748B'>SAC: {hsn_sac_code} • {room_name}</font>",
                    tbl_cell_l,
                ),
                Paragraph(f"{formatted_check_in} to<br/>{formatted_check_out}", tbl_cell_c),
                Paragraph(str(nights), tbl_cell_c),
                Paragraph(str(num_rooms), tbl_cell_c),
                Paragraph(f"{price_per_night:,.2f}", tbl_cell_r),
                Paragraph(f"{taxable_value:,.2f}", tbl_cell_b),
            ],
        ]

        item_table = Table(items_table_data, colWidths=col_widths)
        item_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), DARK),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ("GRID",          (0, 0), (-1, -1), 0.4, CARD_BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 4 * mm))

        # ── 4. LOWER SECTION: GST BREAKDOWN (Left) vs TOTALS & SUMMARY (Right) ──
        has_cgst_sgst = (cgst_rate is not None and cgst_rate > 0) or (tax_rate > 0 and igst_rate is None)
        effective_cgst_rate = float(cgst_rate) if cgst_rate is not None else (tax_rate / 2.0 if tax_rate > 0 else 0.0)
        effective_sgst_rate = float(sgst_rate) if sgst_rate is not None else (tax_rate / 2.0 if tax_rate > 0 else 0.0)
        effective_igst_rate = float(igst_rate) if igst_rate is not None else 0.0

        if tax_amount > 0:
            if effective_igst_rate > 0:
                cgst_amt = 0.0
                sgst_amt = 0.0
                igst_amt = tax_amount
            elif has_cgst_sgst:
                cgst_amt = round(tax_amount / 2.0, 2)
                sgst_amt = round(tax_amount - cgst_amt, 2)
                igst_amt = 0.0
            else:
                cgst_amt = 0.0
                sgst_amt = 0.0
                igst_amt = tax_amount
        else:
            cgst_amt = 0.0
            sgst_amt = 0.0
            igst_amt = 0.0

        left_box_elements = []

        if is_tax_invoice and tax_amount > 0:
            gst_th = ParagraphStyle("gth", fontSize=7, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_CENTER, leading=8.5)
            gst_td_c = ParagraphStyle("gtc", fontSize=7, fontName="Helvetica", textColor=DARK, alignment=TA_CENTER, leading=8.5)
            gst_td_r = ParagraphStyle("gtr", fontSize=7, fontName="Helvetica", textColor=DARK, alignment=TA_RIGHT, leading=8.5)

            if effective_igst_rate > 0:
                gst_table_data = [
                    [
                        Paragraph("SAC", gst_th),
                        Paragraph("Taxable Value", gst_th),
                        Paragraph(f"IGST ({effective_igst_rate:g}%)", gst_th),
                        Paragraph("Total Tax", gst_th),
                    ],
                    [
                        Paragraph(str(hsn_sac_code), gst_td_c),
                        Paragraph(f"{currency} {taxable_value:,.2f}", gst_td_r),
                        Paragraph(f"{currency} {igst_amt:,.2f}", gst_td_r),
                        Paragraph(f"{currency} {tax_amount:,.2f}", gst_td_r),
                    ],
                ]
                gst_col_w = [18*mm, 28*mm, 28*mm, 26*mm]
            else:
                gst_table_data = [
                    [
                        Paragraph("SAC", gst_th),
                        Paragraph("Taxable Value", gst_th),
                        Paragraph(f"CGST ({effective_cgst_rate:g}%)", gst_th),
                        Paragraph(f"SGST ({effective_sgst_rate:g}%)", gst_th),
                        Paragraph("Total Tax", gst_th),
                    ],
                    [
                        Paragraph(str(hsn_sac_code), gst_td_c),
                        Paragraph(f"{currency} {taxable_value:,.2f}", gst_td_r),
                        Paragraph(f"{currency} {cgst_amt:,.2f}", gst_td_r),
                        Paragraph(f"{currency} {sgst_amt:,.2f}", gst_td_r),
                        Paragraph(f"{currency} {tax_amount:,.2f}", gst_td_r),
                    ],
                ]
                gst_col_w = [16*mm, 24*mm, 21*mm, 21*mm, 22*mm]

            gst_tax_table = Table(gst_table_data, colWidths=gst_col_w)
            gst_tax_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY_LIGHT),
                ("GRID",          (0, 0), (-1, -1), 0.3, CARD_BORDER),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 2),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
            ]))

            left_box_elements.append(
                Paragraph(
                    "<font size=8 color='#0F2937'><b>GST Tax Annexure (SAC 996311)</b></font>",
                    ParagraphStyle("gst_title", leading=9),
                )
            )
            left_box_elements.append(Spacer(1, 1 * mm))
            left_box_elements.append(gst_tax_table)
            left_box_elements.append(Spacer(1, 2 * mm))

        # Amount in Words
        words_str = _amount_to_words(total_amount, currency)
        left_box_elements.append(
            Paragraph(
                f"<font size=7.5 color='#64748B'><b>Amount in Words:</b></font><br/>"
                f"<font size=8 color='#0F2937'><i>{words_str}</i></font>",
                ParagraphStyle("amt_words", leading=10),
            )
        )

        special_reqs = booking_data.get("special_requests")
        if special_reqs:
            left_box_elements.append(Spacer(1, 1.5 * mm))
            left_box_elements.append(
                Paragraph(
                    f"<font size=7 color='#64748B'><b>Special Requests:</b> {special_reqs}</font>",
                    ParagraphStyle("spec_req", leading=9),
                )
            )

        # Right Column: Totals Summary
        tot_label = ParagraphStyle("tl", fontSize=8, fontName="Helvetica", textColor=DARK, alignment=TA_RIGHT, leading=11)
        tot_val   = ParagraphStyle("tv", fontSize=8, fontName="Helvetica", textColor=DARK, alignment=TA_RIGHT, leading=11)
        tot_grand_lbl = ParagraphStyle("tgl", fontSize=9, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT, leading=12)
        tot_grand_val = ParagraphStyle("tgv", fontSize=10, fontName="Helvetica-Bold", textColor=PRIMARY_DARK, alignment=TA_RIGHT, leading=13)

        totals_rows = [
            [Paragraph("Taxable Subtotal:", tot_label), Paragraph(f"{currency} {taxable_value:,.2f}", tot_val)],
        ]
        if discount_amount > 0:
            totals_rows.append(
                [
                    Paragraph("Discount Applied:", tot_label),
                    Paragraph(f"− {currency} {discount_amount:,.2f}", ParagraphStyle("tdisc", parent=tot_val, textColor=GREEN_PAID)),
                ]
            )
        if tax_amount > 0:
            if effective_igst_rate > 0:
                totals_rows.append(
                    [Paragraph(f"IGST ({effective_igst_rate:g}%):", tot_label), Paragraph(f"+ {currency} {igst_amt:,.2f}", tot_val)]
                )
            elif has_cgst_sgst:
                totals_rows.append(
                    [Paragraph(f"CGST ({effective_cgst_rate:g}%):", tot_label), Paragraph(f"+ {currency} {cgst_amt:,.2f}", tot_val)]
                )
                totals_rows.append(
                    [Paragraph(f"SGST ({effective_sgst_rate:g}%):", tot_label), Paragraph(f"+ {currency} {sgst_amt:,.2f}", tot_val)]
                )
            else:
                totals_rows.append(
                    [Paragraph(f"GST ({tax_rate:g}%):", tot_label), Paragraph(f"+ {currency} {tax_amount:,.2f}", tot_val)]
                )

        totals_rows.append(
            [Paragraph("<b>Grand Total:</b>", tot_grand_lbl), Paragraph(f"<b>{currency} {total_amount:,.2f}</b>", tot_grand_val)]
        )

        totals_subtable = Table(totals_rows, colWidths=[42*mm, 36*mm])
        totals_subtable.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LINEABOVE",     (0, -1), (-1, -1), 1.2, DARK),
            ("BACKGROUND",    (0, -1), (-1, -1), LIGHT_BG),
            ("TOPPADDING",    (0, -1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 4),
        ]))

        right_box_elements = [
            totals_subtable,
            Spacer(1, 1.5 * mm),
            Paragraph(
                f"<font size=7 color='#16A34A'><b>Payment Mode:</b> Online (Prepaid)</font><br/>"
                f"<font size=6.5 color='#64748B'>{'* Rate is inclusive of all taxes' if is_tax_inclusive else '* Inclusive of applicable GST'}</font>",
                ParagraphStyle("pay_note", alignment=TA_RIGHT, leading=8.5),
            ),
        ]

        summary_container = Table(
            [[left_box_elements, right_box_elements]],
            colWidths=[PAGE_W * 0.57, PAGE_W * 0.43],
        )
        summary_container.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(summary_container)
        story.append(Spacer(1, 4 * mm))

        # ── 5. POLICIES, TERMS & VERIFICATION FOOTER ────────────────────────
        story.append(HRFlowable(width="100%", thickness=0.6, color=LINE_BORDER, spaceAfter=2.5 * mm))

        footer_text = (
            f"<b>Thank you for choosing {app_name}!</b>  •  "
            f"<font color='#64748B'>Standard Check-in: {check_in_time} | Standard Check-out: {check_out_time}. "
            "Government-approved photo ID is required for all guests upon arrival.<br/>"
            f"SAC 996311: Short-stay accommodation services. "
            "This is a digitally generated tax invoice and does not require a physical signature.</font>"
        )
        story.append(Paragraph(
            footer_text,
            ParagraphStyle(
                "footer_style",
                fontSize=7,
                leading=9.5,
                textColor=DARK,
                alignment=TA_CENTER,
            ),
        ))

        doc.build(story)
        return buffer.getvalue()


