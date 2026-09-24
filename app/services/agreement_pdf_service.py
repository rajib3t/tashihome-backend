from __future__ import annotations

import base64
import io
import logging
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# Signature TrueType Font configuration
SIGNATURE_FONTS_MAP: dict[str, dict[str, Any]] = {
    "dancing_script": {"pdf_font": "DancingScript", "file": "DancingScript.ttf", "fallback": "Helvetica-Oblique", "size": 17},
    "great_vibes": {"pdf_font": "GreatVibes", "file": "GreatVibes.ttf", "fallback": "Times-Italic", "size": 19},
    "caveat": {"pdf_font": "Caveat", "file": "Caveat.ttf", "fallback": "Helvetica-Oblique", "size": 18},
    "sacramento": {"pdf_font": "Sacramento", "file": "Sacramento.ttf", "fallback": "Times-Italic", "size": 20},
    "parisienne": {"pdf_font": "Parisienne", "file": "Parisienne.ttf", "fallback": "Helvetica-Oblique", "size": 17},
    "alex_brush": {"pdf_font": "AlexBrush", "file": "AlexBrush.ttf", "fallback": "Times-Italic", "size": 19},
}


def _register_signature_fonts() -> None:
    """Registers TrueType fonts for electronic signatures with ReportLab."""
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
    for key, cfg in SIGNATURE_FONTS_MAP.items():
        pdf_font_name = cfg["pdf_font"]
        font_path = os.path.join(fonts_dir, cfg["file"])
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(pdf_font_name, font_path))
            except Exception as e:
                logger.warning("Failed to register signature font %s: %s", pdf_font_name, e)


_register_signature_fonts()

# Brand palette
PRIMARY = colors.HexColor("#D97706")        # Amber / Gold accent
PRIMARY_DARK = colors.HexColor("#B45309")
PRIMARY_LIGHT = colors.HexColor("#FEF3C7")   # Soft amber tint
DARK = colors.HexColor("#0F2937")           # Deep navy
DARK_HEADER = colors.HexColor("#1E293B")    # Slate 800
LIGHT_BG = colors.HexColor("#F8FAFC")       # Slate 50
CARD_BORDER = colors.HexColor("#E2E8F0")    # Slate 200
LINE_BORDER = colors.HexColor("#CBD5E1")    # Slate 300
TEXT_DARK = colors.HexColor("#0F172A")      # Slate 900
TEXT_MUTED = colors.HexColor("#64748B")     # Slate 500
GREEN_SIGNED = colors.HexColor("#16A34A")   # Emerald 600
GREEN_BG = colors.HexColor("#DCFCE7")       # Emerald 100
WHITE = colors.white

PAGE_W = 186 * mm


DEFAULT_HOST_CLAUSES = [
    {
        "heading": "1. Purpose & Scope of Partnership",
        "body": (
            "This Host Partnership & Service Agreement ('Agreement') governs the terms under which the Host lists "
            "and operates homestay accommodations on the TashiHome platform. TashiHome acts as a technology intermediary "
            "connecting travelers with licensed homestay hosts."
        ),
    },
    {
        "heading": "2. Homestay Standards & Regulatory Compliance",
        "body": (
            "The Host warrants that all listed homestay rooms are clean, hygienic, and compliant with local tourism, "
            "safety, and municipal hospitality guidelines. The Host agrees to maintain proper guest identification "
            "registers (Form C for foreign guests where applicable under Indian law) upon check-in."
        ),
    },
    {
        "heading": "3. Platform Commission & Payment Settlements",
        "body": (
            "TashiHome shall retain the agreed platform service fee percentage on all completed guest bookings. "
            "Net host earnings shall be disbursed directly to the Host's verified bank account or UPI address registered "
            "with TashiHome within 24 hours of successful guest check-in, subject to RazorpayX settlement cycles."
        ),
    },
    {
        "heading": "4. Rate Parity & Booking Fulfillment",
        "body": (
            "The Host agrees not to offer identical rooms to walk-in guests or other distribution channels at rates lower "
            "than those published on the TashiHome platform for the corresponding dates. All confirmed reservations must "
            "be honored without unapproved cancellations."
        ),
    },
    {
        "heading": "5. Cancellation & Guest Refund Policies",
        "body": (
            "Cancellations and refunds shall strictly follow the cancellation policy selected by the Host on the listing. "
            "In the event of an emergency cancellation initiated by the Host, the Host agrees to assist in re-accommodating "
            "affected guests or absorbing platform reallocation charges."
        ),
    },
    {
        "heading": "6. Indemnification & Limitation of Liability",
        "body": (
            "The Host agrees to indemnify and hold harmless TashiHome Technologies, its directors, and affiliates against "
            "any property damage, physical injury, or regulatory penalties occurring on the homestay premises. TashiHome "
            "acts solely as a booking facilitator and is not liable for guest conduct or property disputes."
        ),
    },
]


_LOGO_CACHE: dict[str, bytes] = {}


def _fetch_logo(
    url_or_path: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    max_height: float = 14 * mm,
    max_width: float = 50 * mm,
) -> Optional[Image]:
    """Fetch/load logo image from URL, local path, or raw bytes and return scaled ReportLab Image."""
    data = image_bytes
    if not data and url_or_path:
        if url_or_path in _LOGO_CACHE:
            data = _LOGO_CACHE[url_or_path]
        else:
            try:
                if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
                    req = urllib.request.Request(
                        url_or_path,
                        headers={"User-Agent": "TashiHome-AgreementService/1.0"},
                    )
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        data = resp.read()
                        _LOGO_CACHE[url_or_path] = data
                elif url_or_path.startswith("file://") or url_or_path.startswith("/"):
                    path = url_or_path[7:] if url_or_path.startswith("file://") else url_or_path
                    with open(path, "rb") as f:
                        data = f.read()
                        _LOGO_CACHE[url_or_path] = data
            except Exception as exc:
                logger.warning("Could not fetch agreement logo from %s: %s", url_or_path, exc)
                return None

    if not data:
        return None

    try:
        img = Image(io.BytesIO(data))
        orig_w = getattr(img, "imageWidth", 0)
        orig_h = getattr(img, "imageHeight", 0)
        if orig_w <= 0 or orig_h <= 0:
            return None
        ratio = orig_w / orig_h
        img.drawHeight = max_height
        img.drawWidth = max_height * ratio
        if img.drawWidth > max_width:
            img.drawWidth = max_width
            img.drawHeight = max_width / ratio
        return img
    except Exception as exc:
        logger.warning("Failed to construct ReportLab Image from logo data: %s", exc)
        return None


class AgreementPdfService:
    """Service to generate executed Host Partnership & E-Sign contracts in PDF format using ReportLab."""

    def __init__(self):
        self._styles = self._init_styles()

    def _init_styles(self) -> dict[str, ParagraphStyle]:
        return {
            "title": ParagraphStyle(
                "AgmtTitle",
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=22,
                textColor=DARK,
            ),
            "subtitle": ParagraphStyle(
                "AgmtSubtitle",
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                textColor=TEXT_MUTED,
            ),
            "section_heading": ParagraphStyle(
                "AgmtSectionHeading",
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=15,
                textColor=PRIMARY_DARK,
            ),
            "clause_heading": ParagraphStyle(
                "AgmtClauseHeading",
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
                textColor=DARK_HEADER,
            ),
            "body": ParagraphStyle(
                "AgmtBody",
                fontName="Helvetica",
                fontSize=8.5,
                leading=12.5,
                textColor=TEXT_DARK,
                alignment=TA_JUSTIFY,
            ),
            "body_bold": ParagraphStyle(
                "AgmtBodyBold",
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=12.5,
                textColor=TEXT_DARK,
            ),
            "table_cell": ParagraphStyle(
                "AgmtTableCell",
                fontName="Helvetica",
                fontSize=8,
                leading=11,
                textColor=TEXT_DARK,
            ),
            "table_cell_bold": ParagraphStyle(
                "AgmtTableCellBold",
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=11,
                textColor=TEXT_DARK,
            ),
            "badge_signed": ParagraphStyle(
                "AgmtBadgeSigned",
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=GREEN_SIGNED,
                alignment=TA_CENTER,
            ),
            "audit_text": ParagraphStyle(
                "AgmtAuditText",
                fontName="Helvetica",
                fontSize=7.5,
                leading=10.5,
                textColor=TEXT_MUTED,
            ),
            "footer": ParagraphStyle(
                "AgmtFooter",
                fontName="Helvetica",
                fontSize=7.5,
                leading=10,
                textColor=TEXT_MUTED,
                alignment=TA_CENTER,
            ),
        }

    def get_signature_paragraph_style(self, font_key: Optional[str] = None) -> ParagraphStyle:
        """Returns a ParagraphStyle configured with the requested signature TrueType font or graceful fallback."""
        normalized_key = (font_key or "dancing_script").strip().lower().replace("-", "_").replace(" ", "_")
        cfg = SIGNATURE_FONTS_MAP.get(normalized_key) or SIGNATURE_FONTS_MAP.get("dancing_script", {
            "pdf_font": "Helvetica-Oblique", "fallback": "Helvetica-Oblique", "size": 16
        })
        pdf_font = cfg["pdf_font"]
        try:
            pdfmetrics.getFont(pdf_font)
            font_name = pdf_font
        except Exception:
            font_name = cfg.get("fallback", "Helvetica-Oblique")

        size = cfg.get("size", 17)
        style_key = f"SigFont_{font_name}_{size}"
        if style_key not in self._styles:
            self._styles[style_key] = ParagraphStyle(
                style_key,
                fontName=font_name,
                fontSize=size,
                leading=size + 4,
                textColor=DARK,
            )
        return self._styles[style_key]

    def generate_signed_agreement_pdf(
        self,
        agreement: Any,
        vendor: Any,
        company: Optional[Any] = None,
        address: Optional[Any] = None,
        clauses: Optional[List[Dict[str, str]]] = None,
        logo_url: Optional[str] = None,
        logo_bytes: Optional[bytes] = None,
        operator_info: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """Generate a complete executed agreement PDF and return raw bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
        )

        elements: list = []
        styles = self._styles

        # ── 0. Extract Platform Operator Settings ─────────────────────────────
        operator_info = operator_info or {}
        app_name = operator_info.get("app_name") or "TashiHome"
        tagline = operator_info.get("tagline") or "Authentic Homestays & Community Living"
        legal_name = operator_info.get("legal_name") or f"{app_name} Technologies Pvt. Ltd."
        op_address = operator_info.get("address") or "Gangtok, Sikkim, India"
        op_email = operator_info.get("email") or "partner@tashihomes.in"
        op_phone = operator_info.get("phone") or ""
        op_website = operator_info.get("website") or "www.tashihomes.in"
        doc_title = operator_info.get("title") or "HOST PARTNERSHIP & SERVICE AGREEMENT"

        # ── 1. Header Banner ──────────────────────────────────────────────────
        ref_no = f"AGMT-{str(agreement.public_id)[:8].upper()}"
        signed_dt = agreement.signed_at or datetime.now(timezone.utc)
        date_str = signed_dt.strftime("%d %b %Y, %H:%M:%S UTC")

        logo_img = _fetch_logo(url_or_path=logo_url, image_bytes=logo_bytes)
        brand_cell = []
        if logo_img:
            brand_cell.append(logo_img)
            brand_cell.append(Spacer(1, 1.5 * mm))
        brand_cell.append(
            Paragraph(f"<b>{app_name.upper()}</b><br/><font size='8' color='#64748B'>{tagline}</font>", styles["title"])
        )

        header_data = [
            [
                brand_cell,
                Paragraph(
                    f"<b>AGREEMENT REFERENCE</b><br/>"
                    f"<font color='#B45309'><b>{ref_no}</b></font><br/>"
                    f"Executed Date: {date_str}",
                    ParagraphStyle("HeaderMeta", fontName="Helvetica", fontSize=8, leading=12, alignment=TA_RIGHT),
                ),
            ]
        ]
        header_table = Table(header_data, colWidths=[PAGE_W * 0.55, PAGE_W * 0.45])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=4, spaceAfter=8))

        # Title bar
        elements.append(Paragraph(doc_title.upper(), ParagraphStyle(
            "TitleBar", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=DARK, alignment=TA_CENTER
        )))
        elements.append(Paragraph(
            "This Electronic Agreement is executed pursuant to the Information Technology Act and rules thereunder.",
            ParagraphStyle("SubBar", fontName="Helvetica-Oblique", fontSize=8, leading=11, textColor=TEXT_MUTED, alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 4 * mm))

        # ── 2. Parties Information Card ───────────────────────────────────────
        vendor_name = getattr(agreement, "signer_name", None) or getattr(vendor, "full_name", "Host Partner")
        vendor_email = getattr(agreement, "signer_email", None) or getattr(vendor, "email", "N/A")
        vendor_phone = getattr(agreement, "signer_phone", None) or getattr(vendor, "phone", "N/A")
        company_name = getattr(company, "name", None) or f"{vendor_name}'s Homestay"

        addr_str = "Sikkim, India"
        if address:
            parts = [getattr(address, "address_line1", None), getattr(address, "address_line2", None), getattr(address, "postal_code", None), getattr(address, "country", None)]
            addr_str = ", ".join([p for p in parts if p])

        op_contact_str = f"Contact: {op_email}"
        if op_phone:
            op_contact_str += f" | Phone: {op_phone}"

        parties_data = [
            [
                Paragraph("<b>PLATFORM OPERATOR (FIRST PARTY)</b>", styles["table_cell_bold"]),
                Paragraph("<b>HOMESTAY HOST / VENDOR (SECOND PARTY)</b>", styles["table_cell_bold"]),
            ],
            [
                Paragraph(
                    f"<b>{legal_name}</b><br/>"
                    f"Registered Office: {op_address}<br/>"
                    f"{op_contact_str}<br/>"
                    f"Platform: {op_website}",
                    styles["table_cell"],
                ),
                Paragraph(
                    f"<b>{vendor_name}</b><br/>"
                    f"Homestay / Entity: <b>{company_name}</b><br/>"
                    f"Email: {vendor_email} | Phone: {vendor_phone}<br/>"
                    f"Address: {addr_str}",
                    styles["table_cell"],
                ),
            ],
        ]
        parties_table = Table(parties_data, colWidths=[PAGE_W * 0.5, PAGE_W * 0.5])
        parties_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, CARD_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, CARD_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 4 * mm))

        # ── 3. Commercial Terms Summary ───────────────────────────────────────
        comm_pct = float(getattr(agreement, "commission_percentage", 10.0))
        terms_data = [
            [
                Paragraph("<b>COMMERCIAL SUMMARY</b>", styles["table_cell_bold"]),
                Paragraph("<b>SPECIFICATION</b>", styles["table_cell_bold"]),
            ],
            [
                Paragraph("Platform Commission Rate", styles["table_cell"]),
                Paragraph(f"<b>{comm_pct:.1f}%</b> of booking subtotal per confirmed reservation", styles["table_cell"]),
            ],
            [
                Paragraph("Payout Settlement Cycle", styles["table_cell"]),
                Paragraph("T+24 Hours after verified guest check-in via RazorpayX direct transfer", styles["table_cell"]),
            ],
            [
                Paragraph("Agreement Validity & Renewal", styles["table_cell"]),
                Paragraph("Continuous until terminated by either party with 30 days written notice", styles["table_cell"]),
            ],
        ]
        terms_table = Table(terms_data, colWidths=[PAGE_W * 0.35, PAGE_W * 0.65])
        terms_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_LIGHT),
            ("TEXTCOLOR", (0, 0), (-1, 0), PRIMARY_DARK),
            ("BOX", (0, 0), (-1, -1), 0.5, LINE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(terms_table)
        elements.append(Spacer(1, 4 * mm))

        # ── 4. Agreement Clauses ──────────────────────────────────────────────
        elements.append(Paragraph("TERMS AND CONDITIONS", styles["section_heading"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=LINE_BORDER, spaceBefore=2, spaceAfter=4))

        clauses_to_render = clauses or DEFAULT_HOST_CLAUSES
        for clause in clauses_to_render:
            elements.append(Paragraph(clause["heading"], styles["clause_heading"]))
            elements.append(Paragraph(clause["body"], styles["body"]))
            elements.append(Spacer(1, 2.5 * mm))

        elements.append(Spacer(1, 2 * mm))

        # ── 5. E-Sign & Legal Execution Block ─────────────────────────────────
        elements.append(Paragraph("BILATERAL ELECTRONIC EXECUTION & AUDIT RECORD", styles["section_heading"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=LINE_BORDER, spaceBefore=2, spaceAfter=4))

        # First Party (Platform Operator) Execution Details
        fp_signer_name = getattr(agreement, "first_party_signer_name", None) or "Authorized Signatory"
        fp_signer_role = getattr(agreement, "first_party_signer_role", None) or "Platform Authorized Signatory"
        fp_signed_dt = getattr(agreement, "first_party_signed_at", None) or signed_dt
        fp_date_str = fp_signed_dt.strftime("%d %b %Y, %H:%M:%S UTC") if hasattr(fp_signed_dt, "strftime") else date_str
        fp_sig_data = getattr(agreement, "first_party_signature_data", "") or ""
        fp_sig_type = getattr(agreement, "first_party_signature_type", "digital") or "digital"

        fp_flowable: Any
        if fp_sig_type == "drawn" and fp_sig_data and "base64," in fp_sig_data:
            try:
                raw_b64 = fp_sig_data.split("base64,")[1]
                img_bytes = base64.b64decode(raw_b64)
                fp_flowable = Image(io.BytesIO(img_bytes), width=40 * mm, height=16 * mm)
            except Exception:
                fp_flowable = Paragraph(f"<font size='11'><b><i>{fp_signer_name}</i></b></font>", styles["body_bold"])
        elif fp_sig_type == "typed":
            fp_font = getattr(agreement, "first_party_signature_font", None)
            fp_style = self.get_signature_paragraph_style(fp_font)
            fp_flowable = Paragraph(fp_signer_name, fp_style)
        else:
            fp_flowable = Paragraph(
                f"<font size='10' color='#0F766E'><b>[DIGITALLY COUNTERSIGNED]</b></font><br/>"
                f"<font size='11'><b><i>{fp_signer_name}</i></b></font>",
                styles["body_bold"]
            )

        # Second Party (Homestay Host) Execution Details
        sig_type = getattr(agreement, "signature_type", "typed") or "typed"
        sig_data = getattr(agreement, "signature_data", "") or ""
        sig_font = getattr(agreement, "signature_font", None)

        sig_flowable: Any
        if sig_type == "drawn" and sig_data and "base64," in sig_data:
            try:
                raw_b64 = sig_data.split("base64,")[1]
                img_bytes = base64.b64decode(raw_b64)
                sig_img_buf = io.BytesIO(img_bytes)
                sig_flowable = Image(sig_img_buf, width=45 * mm, height=18 * mm)
            except Exception as e:
                logger.warning("Failed to parse signature image: %s", e)
                sig_flowable = Paragraph(f"<i>{vendor_name}</i>", styles["body_bold"])
        else:
            sig_name = sig_data if (sig_data and not sig_data.startswith("data:")) else vendor_name
            sig_style = self.get_signature_paragraph_style(sig_font)
            sig_flowable = Paragraph(sig_name, sig_style)

        doc_hash = getattr(agreement, "document_hash", "N/A") or "N/A"
        client_ip = getattr(agreement, "signer_ip", "N/A") or "N/A"
        user_agent = getattr(agreement, "signer_user_agent", "N/A") or "N/A"
        if len(user_agent) > 60:
            user_agent = user_agent[:57] + "..."

        sign_table_data = [
            [
                Paragraph(f"<b>FIRST PARTY: {app_name.upper()} PLATFORM</b>", styles["table_cell_bold"]),
                Paragraph("<b>SECOND PARTY: HOST PARTNER</b>", styles["table_cell_bold"]),
            ],
            [
                fp_flowable,
                sig_flowable,
            ],
            [
                Paragraph(
                    f"Signatory: <b>{fp_signer_name}</b><br/>"
                    f"Role: {fp_signer_role}<br/>"
                    f"Entity: <b>{legal_name}</b><br/>"
                    f"Executed: {fp_date_str}",
                    styles["audit_text"],
                ),
                Paragraph(
                    f"Signer: <b>{vendor_name}</b><br/>"
                    f"Email: {vendor_email}<br/>"
                    f"Executed: {date_str}<br/>"
                    f"IP: <b>{client_ip}</b> | Agent: {user_agent}",
                    styles["audit_text"],
                ),
            ],
        ]

        sign_table = Table(sign_table_data, colWidths=[PAGE_W * 0.5, PAGE_W * 0.5])
        sign_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, CARD_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, CARD_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(sign_table)
        elements.append(Spacer(1, 3 * mm))

        # Cryptographic checksum footer
        elements.append(Paragraph(
            f"<b>Cryptographic Integrity Checksum (SHA-256):</b> <font color='#64748B'>{doc_hash}</font>",
            styles["audit_text"],
        ))
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(
            f"Page 1 of 1 — Generated securely by {app_name} Electronic Signature Platform",
            styles["footer"],
        ))

        doc.build(elements)
        return buffer.getvalue()

