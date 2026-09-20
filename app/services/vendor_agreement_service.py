from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.dto.agreements.agreement_dto import (
    AdminCountersignAgreementDTO,
    AgreementQueryDTO,
    SendVendorAgreementDTO,
    SignAgreementDTO,
)
from app.core.config import settings
from app.core.events import EventBus
from app.core.exceptions import AppException
from app.events.events.agreements.agreement_completed_event import AgreementCompletedEvent
from app.events.events.agreements.agreement_invitation_sent_event import AgreementInvitationSentEvent
from app.models.user_model import User
from app.models.vendor_agreement_model import AgreementStatus, AgreementType, VendorAgreement
from app.repositories.base_repository import Page
from app.repositories.vendor_agreement_repository import VendorAgreementRepository
from app.services.agreement_pdf_service import AgreementPdfService, DEFAULT_HOST_CLAUSES
from app.services.email_service import BaseEmailService, EmailAttachment
from app.services.email_template_service import EmailTemplateService
from app.services.setting_service import SettingService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class VendorAgreementService:
    def __init__(
        self,
        repository: VendorAgreementRepository,
        email_service: BaseEmailService,
        email_template_service: EmailTemplateService,
        storage_service: StorageService,
        pdf_service: AgreementPdfService,
        setting_service: Optional[SettingService] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.repository = repository
        self.email_service = email_service
        self.email_template_service = email_template_service
        self.storage_service = storage_service
        self.pdf_service = pdf_service
        self.setting_service = setting_service
        self.event_bus = event_bus

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _get_signing_url(self, token: str) -> str:
        base_url = (settings.FRONTEND_URL or "http://localhost:4200").rstrip("/")
        return f"{base_url}/agreements/{token}"

    def _get_dashboard_url(self) -> str:
        base_url = (settings.FRONTEND_URL or "http://localhost:4200").rstrip("/")
        return f"{base_url}/vendor"

    async def get_operator_info(self) -> Dict[str, Any]:
        """Fetch platform operator settings for agreements with fallbacks."""
        info = {
            "app_name": "TashiHome",
            "tagline": "Authentic Homestays & Community Living",
            "legal_name": "TashiHome Technologies Pvt. Ltd.",
            "address": "Gangtok, Sikkim, India",
            "email": settings.EMAILS_FROM_EMAIL or "partner@tashihomes.in",
            "phone": "",
            "website": (settings.FRONTEND_URL or "https://tashihomes.in").replace("https://", "").replace("http://", "").rstrip("/"),
            "title": "HOST PARTNERSHIP & SERVICE AGREEMENT",
            "logo_url": None,
        }
        if not self.setting_service:
            return info

        try:
            app_name = await self.setting_service.get_value("app_name")
            if app_name:
                info["app_name"] = app_name

            legal_name = (
                await self.setting_service.get_value("agreement_company_legal_name")
                or await self.setting_service.get_value("legal_name")
            )
            if legal_name:
                info["legal_name"] = legal_name
            elif app_name:
                info["legal_name"] = f"{app_name} Technologies Pvt. Ltd."

            address = (
                await self.setting_service.get_value("agreement_company_address")
                or await self.setting_service.get_value("contact_address")
            )
            if address:
                info["address"] = address

            email = await self.setting_service.get_value("contact_email")
            if email:
                info["email"] = email

            phone = await self.setting_service.get_value("contact_phone")
            if phone:
                info["phone"] = phone

            title = await self.setting_service.get_value("agreement_title")
            if title:
                info["title"] = title

            # Resolve logo URL from agreement_logo, app_logo, or white_logo
            logo_key = (
                await self.setting_service.get_value("agreement_logo")
                or await self.setting_service.get_value("app_logo")
                or await self.setting_service.get_value("white_logo")
            )
            if logo_key:
                info["logo_url"] = await self.storage_service.get_display_url(logo_key)
        except Exception as exc:
            logger.warning("Could not resolve operator settings for agreements: %s", exc)

        return info

    async def get_agreement_template_clauses(self) -> List[Dict[str, str]]:
        """Fetch dynamic agreement template clauses from settings or return defaults."""
        if not self.setting_service:
            return list(DEFAULT_HOST_CLAUSES)

        try:
            custom_template = await self.setting_service.get_value("agreement_template_terms")
            if custom_template and custom_template.strip():
                try:
                    parsed = json.loads(custom_template)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed
                except Exception:
                    # Treat as single formatted body if not JSON
                    return [
                        {
                            "heading": "Terms & Conditions",
                            "body": custom_template.strip(),
                        }
                    ]
        except Exception as exc:
            logger.warning("Failed to load custom agreement template from settings: %s", exc)

        return list(DEFAULT_HOST_CLAUSES)

    def _build_email_common_data(self, operator_info: Dict[str, Any]) -> Dict[str, str]:
        """Prepare setting-driven branding and company details for email templates."""
        app_name = operator_info.get("app_name") or "TashiHome"
        logo_url = operator_info.get("logo_url") or ""
        legal_name = operator_info.get("legal_name") or f"{app_name} Technologies Private Limited"
        legal_address = operator_info.get("address") or "Sikkim, India"
        support_email = operator_info.get("email") or settings.EMAILS_FROM_EMAIL or "partner@tashihomes.in"
        header_logo_html = (
            f'<img src="{logo_url}" alt="{app_name}" style="display:block; max-height:48px; max-width:180px; height:auto; width:auto; border:0; margin:0 auto 10px;" />\n'
            f'<h1 style="margin:0; font-size:24px; font-weight:700; color:#FFFFFF; letter-spacing:0.5px;">{app_name}</h1>'
            if logo_url
            else f'<h1 style="margin:0; font-size:24px; font-weight:700; color:#FFFFFF; letter-spacing:0.5px;">{app_name}</h1>'
        )
        return {
            "app_name": app_name,
            "logo_url": logo_url,
            "logo_display": "block" if logo_url else "none",
            "header_logo_html": header_logo_html,
            "legal_name": legal_name,
            "legal_address": legal_address,
            "support_email": support_email,
            "year": str(datetime.now(timezone.utc).year),
        }

    async def create_and_send_agreement(
        self,
        vendor: User,
        host_request_id: Optional[int] = None,
        commission_percentage: Optional[float] = None,
        valid_days: int = 7,
        custom_notes: Optional[str] = None,
        created_by_id: Optional[int] = None,
        commit: bool = False,
    ) -> VendorAgreement:
        """Create a new vendor agreement session, persist it, and dispatch the invitation email."""
        operator_info = await self.get_operator_info()

        # Resolve commission percentage
        if commission_percentage is not None:
            comm_pct = commission_percentage
        else:
            setting_comm = None
            if self.setting_service:
                val = await self.setting_service.get_value("default_commission_percentage")
                if val:
                    try:
                        setting_comm = float(val)
                    except ValueError:
                        pass
            comm_pct = (
                setting_comm
                if setting_comm is not None
                else getattr(settings, "DEFAULT_COMMISSION_PERCENTAGE", 10.0)
            )

        # Resolve valid days from setting if default 7 was used
        if valid_days == 7 and self.setting_service:
            days_str = await self.setting_service.get_value("agreement_default_expiry_days")
            if days_str:
                try:
                    valid_days = int(days_str)
                except ValueError:
                    pass

        token = self._generate_token()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=valid_days)

        # Dynamic setting-driven template clauses
        terms_clauses = await self.get_agreement_template_clauses()
        if custom_notes:
            terms_clauses.append({
                "heading": "Special Terms & Annexures",
                "body": custom_notes,
            })

        app_name = operator_info.get("app_name", "TashiHome")
        doc_title = operator_info.get("title", "Host Partnership Agreement")
        legal_name = operator_info.get("legal_name") or f"{app_name} Technologies Pvt. Ltd."

        agreement = VendorAgreement(
            vendor_id=vendor.id,
            host_request_id=host_request_id,
            agreement_type=AgreementType.HOST_ONBOARDING,
            title=f"{doc_title} - {vendor.full_name or 'Host'}",
            version="1.0",
            status=AgreementStatus.SENT,
            token=token,
            commission_percentage=comm_pct,
            expires_at=expires_at,
            sent_at=now,
            terms_snapshot=json.dumps(terms_clauses),
            created_by=created_by_id,
            first_party_signer_name=legal_name,
            first_party_signer_role="Platform Authorized Signatory",
            first_party_signature_type="digital",
            first_party_signature_data=f"Digitally Executed by {legal_name}",
            first_party_signed_at=now,
            first_party_signer_ip="127.0.0.1",
        )
        agreement.vendor = vendor

        saved = await self.repository.create(agreement, commit=commit)

        # Dispatch invitation email asynchronously via Domain Event
        await self._emit_agreement_invitation(
            agreement=saved,
            recipient_name=vendor.full_name or "Host Partner",
            recipient_email=vendor.email,
            operator_info=operator_info,
            valid_days=valid_days,
        )

        return saved

    async def get_by_token(self, token: str) -> VendorAgreement:
        """Fetch agreement by token for public signing; transition to VIEWED on first access."""
        agreement = await self.repository.get_by_token(token)
        if not agreement:
            raise AppException(
                status_code=404,
                message="Agreement link not found or invalid.",
                error_code="AGREEMENT_NOT_FOUND",
                field="token",
            )

        now = datetime.now(timezone.utc)
        if agreement.expires_at < now and agreement.status != AgreementStatus.SIGNED:
            agreement.status = AgreementStatus.EXPIRED
            await self.repository.update(agreement)
            raise AppException(
                status_code=410,
                message="This agreement link has expired. Please contact support or your administrator.",
                error_code="AGREEMENT_EXPIRED",
                field="token",
            )

        # Mark viewed if first view
        if agreement.status == AgreementStatus.SENT:
            agreement.status = AgreementStatus.VIEWED
            agreement.viewed_at = now
            await self.repository.update(agreement)

        return agreement

    async def sign_agreement(
        self,
        token: str,
        sign_dto: SignAgreementDTO,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        authenticated_user_id: Optional[int] = None,
        authenticated_user_role: Optional[str] = None,
    ) -> VendorAgreement:
        """Execute electronic signature, generate PDF, upload to S3, and dispatch confirmation."""
        agreement = await self.repository.get_by_token(token)
        if not agreement:
            raise AppException(
                status_code=404,
                message="Agreement not found.",
                error_code="AGREEMENT_NOT_FOUND",
                field="token",
            )

        # Non-repudiation security: If an authenticated session is present, verify ownership
        if authenticated_user_id is not None:
            is_owner = agreement.vendor_id == authenticated_user_id
            if not is_owner:
                raise AppException(
                    status_code=403,
                    message="You are not authorized to sign this agreement. Please log in with the assigned host account.",
                    error_code="SIGNER_MISMATCH",
                )

        if agreement.status == AgreementStatus.SIGNED:
            raise AppException(
                status_code=400,
                message="This agreement has already been electronically signed.",
                error_code="AGREEMENT_ALREADY_SIGNED",
                field="token",
            )

        now = datetime.now(timezone.utc)
        if agreement.expires_at < now:
            agreement.status = AgreementStatus.EXPIRED
            await self.repository.update(agreement)
            raise AppException(
                status_code=410,
                message="Agreement has expired and cannot be signed.",
                error_code="AGREEMENT_EXPIRED",
                field="token",
            )

        if not sign_dto.terms_accepted or not sign_dto.consent_acknowledged:
            raise AppException(
                status_code=422,
                message="You must read and accept the terms and legal consent.",
                error_code="CONSENT_REQUIRED",
                field="terms_accepted",
            )

        signer_name = sign_dto.signer_name.strip()
        if not signer_name:
            raise AppException(
                status_code=422,
                message="Signer legal name is required.",
                error_code="SIGNER_NAME_REQUIRED",
                field="signer_name",
            )

        # Compute SHA-256 integrity hash
        hash_seed = f"{agreement.public_id}:{token}:{signer_name}:{client_ip or 'unknown'}:{now.isoformat()}"
        doc_hash = hashlib.sha256(hash_seed.encode("utf-8")).hexdigest()

        # Update agreement model fields
        agreement.signer_name = signer_name
        agreement.signer_email = agreement.vendor.email if agreement.vendor else None
        agreement.signer_phone = agreement.vendor.phone if agreement.vendor else None
        agreement.signature_type = sign_dto.signature_type
        agreement.signature_data = sign_dto.signature_data
        agreement.signer_ip = client_ip
        agreement.signer_user_agent = user_agent
        agreement.document_hash = doc_hash
        agreement.signed_at = now

        # Update bilateral execution status
        if agreement.is_first_party_signed:
            agreement.status = AgreementStatus.SIGNED
        else:
            agreement.status = AgreementStatus.PARTIALLY_SIGNED

        # Parse clauses if available
        clauses = None
        if agreement.terms_snapshot:
            try:
                clauses = json.loads(agreement.terms_snapshot)
            except Exception:
                clauses = None

        # Generate signed PDF with setting-driven logo and operator info
        vendor = getattr(agreement, "vendor", None)
        company = getattr(vendor, "company", None) if vendor else None
        address = None
        if company:
            try:
                addrs = getattr(company, "addresses", None)
                if addrs:
                    address = addrs[0]
            except Exception:
                pass
        if not address and vendor:
            try:
                u_addrs = getattr(vendor, "addresses", None)
                if u_addrs:
                    address = u_addrs[0]
            except Exception:
                pass

        operator_info = await self.get_operator_info()
        logo_url = operator_info.get("logo_url")
        app_name = operator_info.get("app_name", "TashiHome")

        pdf_bytes = self.pdf_service.generate_signed_agreement_pdf(
            agreement=agreement,
            vendor=agreement.vendor,
            company=company,
            address=address,
            clauses=clauses,
            logo_url=logo_url,
            operator_info=operator_info,
        )

        # Upload to S3 / MinIO
        s3_key = f"agreements/{agreement.public_id}/Host_Agreement_{signer_name.replace(' ', '_')}.pdf"
        try:
            await self.storage_service.upload_bytes(
                key=s3_key,
                data=pdf_bytes,
                content_type="application/pdf",
            )
            agreement.pdf_file_url = s3_key
        except Exception as exc:
            logger.error("Failed to upload executed agreement PDF to storage: %s", exc)
            agreement.pdf_file_url = s3_key  # persist key for retry

        # Activate vendor user & mark terms accepted
        if agreement.vendor:
            agreement.vendor.is_terms_accepted = True
            self.repository.db.add(agreement.vendor)

        await self.repository.update(agreement)

        # Dispatch completion email asynchronously via Domain Event
        await self._emit_agreement_completed(
            agreement=agreement,
            pdf_bytes=pdf_bytes,
            operator_info=operator_info,
            signer_name=signer_name,
        )

        return agreement

    async def list_agreements(self, params: AgreementQueryDTO) -> Page[VendorAgreement]:
        return await self.repository.list_agreements(params)

    async def get_by_public_id(self, public_id: UUID | str) -> Optional[VendorAgreement]:
        return await self.repository.get_by_public_id(public_id)

    async def resend_agreement(self, agreement_id: UUID | str, valid_days: int = 7) -> VendorAgreement:
        agreement = await self.repository.get_by_public_id(agreement_id)
        if not agreement:
            raise AppException(
                status_code=404,
                message="Agreement not found.",
                error_code="AGREEMENT_NOT_FOUND",
                field="agreement_id",
            )

        if agreement.status == AgreementStatus.SIGNED:
            raise AppException(
                status_code=400,
                message="Agreement is already signed and cannot be resent.",
                error_code="AGREEMENT_ALREADY_SIGNED",
            )

        # Renew token & expiry
        token = self._generate_token()
        now = datetime.now(timezone.utc)
        agreement.token = token
        agreement.expires_at = now + timedelta(days=valid_days)
        agreement.status = AgreementStatus.SENT
        agreement.sent_at = now

        await self.repository.update(agreement)

        if agreement.vendor:
            operator_info = await self.get_operator_info()
            await self._emit_agreement_invitation(
                agreement=agreement,
                recipient_name=agreement.vendor.full_name or "Host Partner",
                recipient_email=agreement.vendor.email,
                operator_info=operator_info,
                valid_days=valid_days,
            )

        return agreement

    async def countersign_agreement(
        self,
        agreement_id: UUID | str,
        admin_user: Any,
        data: Optional[AdminCountersignAgreementDTO] = None,
        client_ip: Optional[str] = None,
    ) -> VendorAgreement:
        """Execute First Party (Platform / Admin) signature on an agreement."""
        agreement = await self.repository.get_by_public_id(agreement_id)
        if not agreement:
            raise AppException(
                status_code=404,
                message="Agreement not found.",
                error_code="AGREEMENT_NOT_FOUND",
                field="agreement_id",
            )

        now = datetime.now(timezone.utc)
        signer_name = (
            (data.signer_name if data and data.signer_name else None)
            or getattr(admin_user, "full_name", None)
            or "Platform Authorized Signatory"
        )
        signer_role = (
            (data.signer_role if data and data.signer_role else None)
            or "Platform Authorized Signatory"
        )
        sig_type = (data.signature_type if data and data.signature_type else None) or "digital"
        sig_data = (data.signature_data if data and data.signature_data else None) or f"Digitally Countersigned by {signer_name}"

        agreement.first_party_signer_name = signer_name
        agreement.first_party_signer_role = signer_role
        agreement.first_party_signature_type = sig_type
        agreement.first_party_signature_data = sig_data
        agreement.first_party_signed_at = now
        agreement.first_party_signer_ip = client_ip or "127.0.0.1"

        # Update bilateral execution status
        if agreement.is_second_party_signed:
            agreement.status = AgreementStatus.SIGNED
        else:
            agreement.status = AgreementStatus.SENT

        operator_info = await self.get_operator_info()

        # If both parties have signed, regenerate final executed PDF and notify
        if agreement.is_bilateral_signed:
            vendor = getattr(agreement, "vendor", None)
            company = getattr(vendor, "company", None) if vendor else None
            address = None
            if company:
                try:
                    addrs = getattr(company, "addresses", None)
                    if addrs:
                        address = addrs[0]
                except Exception:
                    pass

            clauses = None
            if agreement.terms_snapshot:
                try:
                    clauses = json.loads(agreement.terms_snapshot)
                except Exception:
                    pass

            pdf_bytes = self.pdf_service.generate_signed_agreement_pdf(
                agreement=agreement,
                vendor=agreement.vendor,
                company=company,
                address=address,
                clauses=clauses,
                logo_url=operator_info.get("logo_url"),
                operator_info=operator_info,
            )

            s3_key = f"agreements/{agreement.public_id}/Host_Agreement_{(agreement.signer_name or 'Host').replace(' ', '_')}.pdf"
            try:
                await self.storage_service.upload_bytes(
                    key=s3_key,
                    data=pdf_bytes,
                    content_type="application/pdf",
                )
                agreement.pdf_file_url = s3_key
            except Exception as exc:
                logger.error("Failed to upload countersigned agreement PDF: %s", exc)

            if agreement.vendor:
                agreement.vendor.is_terms_accepted = True
                self.repository.db.add(agreement.vendor)

            await self._emit_agreement_completed(
                agreement=agreement,
                pdf_bytes=pdf_bytes,
                operator_info=operator_info,
                signer_name=agreement.signer_name,
            )

        await self.repository.update(agreement)
        return agreement

    async def cancel_agreement(self, agreement_id: UUID | str) -> VendorAgreement:
        agreement = await self.repository.get_by_public_id(agreement_id)
        if not agreement:
            raise AppException(
                status_code=404,
                message="Agreement not found.",
                error_code="AGREEMENT_NOT_FOUND",
                field="agreement_id",
            )

        if agreement.status == AgreementStatus.SIGNED:
            raise AppException(
                status_code=400,
                message="Cannot cancel an already signed agreement.",
                error_code="AGREEMENT_ALREADY_SIGNED",
            )

        agreement.status = AgreementStatus.CANCELLED
        await self.repository.update(agreement)
        return agreement

    async def get_download_url(self, agreement: VendorAgreement) -> Optional[str]:
        if not agreement.pdf_file_url:
            return None
        return await self.storage_service.generate_presigned_url(agreement.pdf_file_url)

    # ── Asynchronous Event Dispatch & Direct Fallbacks ─────────────────────────

    async def _emit_agreement_invitation(
        self,
        agreement: VendorAgreement,
        recipient_name: str,
        recipient_email: str,
        operator_info: Dict[str, Any],
        valid_days: int,
    ) -> None:
        """Publish AgreementInvitationSentEvent via Redis EventBus; fallback to direct email send."""
        dispatched_event = False
        if self.event_bus:
            try:
                await self.event_bus.publish(
                    AgreementInvitationSentEvent(
                        agreement=agreement,
                        recipient_name=recipient_name,
                        recipient_email=recipient_email,
                    )
                )
                dispatched_event = True
                logger.info("Published AgreementInvitationSentEvent for %s", recipient_email)
            except Exception as exc:
                logger.warning("Event bus publish failed for agreement invitation: %s. Falling back to direct email.", exc)

        if not dispatched_event:
            await self._send_invitation_email_direct(agreement, recipient_name, recipient_email, operator_info, valid_days)

    async def _send_invitation_email_direct(
        self,
        agreement: VendorAgreement,
        recipient_name: str,
        recipient_email: str,
        operator_info: Dict[str, Any],
        valid_days: int,
    ) -> None:
        """Synchronous fallback to render and send agreement invitation email."""
        try:
            vendor = getattr(agreement, "vendor", None)
            company_name = (
                getattr(vendor, "company", None).name
                if vendor and getattr(vendor, "company", None)
                else f"{recipient_name}'s Homestay"
            )
            signing_url = self._get_signing_url(agreement.token)
            app_name = operator_info.get("app_name", "TashiHome")
            comm_pct = float(agreement.commission_percentage) if getattr(agreement, "commission_percentage", None) is not None else 10.0
            common_data = self._build_email_common_data(operator_info)
            template_data = {
                **common_data,
                "host_name": recipient_name,
                "company_name": company_name,
                "signing_url": signing_url,
                "commission_percentage": f"{comm_pct:.1f}",
                "expires_in_days": str(valid_days),
            }
            html_content = await self.email_template_service.render_template(
                "host_agreement_invitation",
                template_data,
                strict=False,
            )
            await self.email_service.send_email(
                to_email=recipient_email,
                subject=f"Action Required: Review & E-Sign Your {app_name} Host Agreement",
                text=f"Please review and electronically sign your {app_name} Host Partnership Agreement here: {signing_url}",
                html=html_content,
            )
        except Exception as exc:
            logger.warning("Direct invitation email dispatch failed for %s: %s", recipient_email, exc)

    async def _emit_agreement_completed(
        self,
        agreement: VendorAgreement,
        pdf_bytes: Optional[bytes] = None,
        operator_info: Optional[Dict[str, Any]] = None,
        signer_name: Optional[str] = None,
    ) -> None:
        """Publish AgreementCompletedEvent via Redis EventBus; fallback to direct email send."""
        dispatched_event = False
        if self.event_bus:
            try:
                pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8") if pdf_bytes else None
                await self.event_bus.publish(
                    AgreementCompletedEvent(
                        agreement=agreement,
                        pdf_bytes_b64=pdf_b64,
                    )
                )
                dispatched_event = True
                logger.info("Published AgreementCompletedEvent for agreement %s", agreement.public_id)
            except Exception as exc:
                logger.warning("Event bus publish failed for agreement completion: %s. Falling back to direct email.", exc)

        if not dispatched_event:
            await self._send_completed_email_direct(agreement, pdf_bytes, signer_name, operator_info)

    async def _send_completed_email_direct(
        self,
        agreement: VendorAgreement,
        pdf_bytes: Optional[bytes] = None,
        signer_name: Optional[str] = None,
        operator_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Synchronous fallback to render and send executed agreement email."""
        try:
            operator_info = operator_info or await self.get_operator_info()
            app_name = operator_info.get("app_name", "TashiHome")
            vendor = getattr(agreement, "vendor", None)
            recipient_email = agreement.signer_email or (vendor.email if vendor else None)
            if not recipient_email:
                return

            host_name = signer_name or agreement.signer_name or (vendor.full_name if vendor else "Host Partner")
            agreement_view_url = f"{self._get_dashboard_url()}/agreements"
            common_data = self._build_email_common_data(operator_info)
            template_data = {
                **common_data,
                "host_name": host_name,
                "company_name": (getattr(vendor, "company", None).name if vendor and getattr(vendor, "company", None) else "Homestay"),
                "agreement_ref": f"AGMT-{str(agreement.public_id)[:8].upper()}",
                "signed_date": (agreement.signed_at.strftime("%d %b %Y, %H:%M:%S UTC") if agreement.signed_at and hasattr(agreement.signed_at, "strftime") else "Recently"),
                "pdf_download_url": agreement_view_url,
                "agreement_view_url": agreement_view_url,
                "dashboard_url": self._get_dashboard_url(),
            }
            html_content = await self.email_template_service.render_template(
                "host_agreement_completed",
                template_data,
                strict=False,
            )

            attachments: list[EmailAttachment] = []
            if pdf_bytes:
                attachments.append(
                    EmailAttachment(
                        filename=f"{app_name.replace(' ', '_')}_Host_Agreement_{agreement.public_id}.pdf",
                        content=pdf_bytes,
                        mimetype="application/pdf",
                    )
                )

            await self.email_service.send_email(
                to_email=recipient_email,
                subject=f"{app_name} Host Agreement Executed - Welcome {host_name}!",
                text=f"Your Host Agreement has been successfully signed. View your executed agreement: {agreement_view_url}",
                html=html_content,
                attachments=attachments if attachments else None,
            )
        except Exception as exc:
            logger.warning("Direct completed email dispatch failed: %s", exc)


