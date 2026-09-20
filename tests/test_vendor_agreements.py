import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid


from app.application.dto.agreements.agreement_dto import (
    SendVendorAgreementDTO,
    SignAgreementDTO,
)
from app.application.dto.vendors.vendor import AdminOnboardHostDTO
from app.application.use_case.admin.vendors.onboard_host_use_case import AdminOnboardHostUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import User, UserRole, UserStatus
from app.models.vendor_agreement_model import AgreementStatus, AgreementType, VendorAgreement
from app.schemas.vendor_schema import VendorUserResponseData
from app.services.agreement_pdf_service import AgreementPdfService
from app.services.email_template_service import EmailTemplateService
from app.services.vendor_agreement_service import VendorAgreementService


def test_sql_enum_compilation():
    """Verify that SQLAlchemy compiles AgreementType to lowercase value 'host_onboarding'."""
    from sqlalchemy import insert
    from sqlalchemy.dialects import postgresql
    stmt = insert(VendorAgreement).values(
        agreement_type=AgreementType.HOST_ONBOARDING,
        status=AgreementStatus.SENT,
    )
    compiled = stmt.compile(dialect=postgresql.dialect())
    assert compiled.params["agreement_type"] == "host_onboarding"
    assert compiled.params["status"] == "sent"


def test_agreement_pdf_generation_bytes():
    """Test that AgreementPdfService generates a valid PDF starting with %PDF- header."""
    pdf_service = AgreementPdfService()

    mock_vendor = MagicMock()
    mock_vendor.full_name = "Karma Tenzin"
    mock_vendor.email = "karma@example.com"
    mock_vendor.phone = "+919876543210"

    mock_company = MagicMock()
    mock_company.name = "Tenzin Heritage Homestay"

    mock_agreement = MagicMock()
    mock_agreement.public_id = uuid.uuid4()
    mock_agreement.signer_name = "Karma Tenzin"
    mock_agreement.signer_email = "karma@example.com"
    mock_agreement.signer_phone = "+919876543210"
    mock_agreement.commission_percentage = 10.0
    mock_agreement.signed_at = datetime.now(timezone.utc)
    mock_agreement.signature_type = "typed"
    mock_agreement.signature_data = "Karma Tenzin"
    mock_agreement.document_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    mock_agreement.signer_ip = "192.168.1.1"
    mock_agreement.signer_user_agent = "Mozilla/5.0 Test Browser"

    pdf_bytes = pdf_service.generate_signed_agreement_pdf(
        agreement=mock_agreement,
        vendor=mock_vendor,
        company=mock_company,
        address=None,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")


def test_create_and_send_agreement():
    """Test creating and sending agreement invitation email."""
    async def run_test():
        repo = AsyncMock()
        email_service = AsyncMock()
        template_service = AsyncMock()
        template_service.render_template.return_value = "<html>Invitation</html>"
        storage_service = AsyncMock()
        pdf_service = MagicMock()

        service = VendorAgreementService(
            repository=repo,
            email_service=email_service,
            email_template_service=template_service,
            storage_service=storage_service,
            pdf_service=pdf_service,
        )

        mock_user = MagicMock()
        mock_user.id = 42
        mock_user.email = "host@test.com"
        mock_user.full_name = "Host Partner"
        mock_user.company = MagicMock(name="My Homestay")

        repo.create.side_effect = lambda agmt, commit=False: agmt

        agreement = await service.create_and_send_agreement(
            vendor=mock_user,
            commission_percentage=12.5,
            valid_days=5,
            custom_notes="Special winter clause",
            created_by_id=1,
            commit=True,
        )

        assert agreement.vendor_id == 42
        assert float(agreement.commission_percentage) == 12.5
        assert agreement.status == AgreementStatus.SENT
        assert len(agreement.token) >= 32
        assert repo.create.called
        assert email_service.send_email.called
        call_kwargs = email_service.send_email.call_args.kwargs
        assert call_kwargs["to_email"] == "host@test.com"
        assert "E-Sign" in call_kwargs["subject"]

    asyncio.run(run_test())


def test_get_public_agreement_by_token_and_mark_viewed():
    """Test public token lookup transitions status from SENT to VIEWED."""
    async def run_test():
        repo = AsyncMock()
        email_service = AsyncMock()
        template_service = AsyncMock()
        storage_service = AsyncMock()
        pdf_service = MagicMock()

        service = VendorAgreementService(
            repository=repo,
            email_service=email_service,
            email_template_service=template_service,
            storage_service=storage_service,
            pdf_service=pdf_service,
        )

        mock_agmt = MagicMock()
        mock_agmt.token = "valid-token-123"
        mock_agmt.status = AgreementStatus.SENT
        mock_agmt.expires_at = datetime.now(timezone.utc) + timedelta(days=3)
        mock_agmt.terms_snapshot = None

        repo.get_by_token.return_value = mock_agmt

        result = await service.get_by_token("valid-token-123")
        assert result.status == AgreementStatus.VIEWED
        assert result.viewed_at is not None
        assert repo.update.called

    asyncio.run(run_test())


def test_get_public_agreement_expired():
    """Test accessing an expired agreement raises 410 error."""
    async def run_test():
        repo = AsyncMock()
        service = VendorAgreementService(
            repository=repo,
            email_service=AsyncMock(),
            email_template_service=AsyncMock(),
            storage_service=AsyncMock(),
            pdf_service=MagicMock(),
        )

        mock_agmt = MagicMock()
        mock_agmt.token = "expired-token-123"
        mock_agmt.status = AgreementStatus.SENT
        mock_agmt.expires_at = datetime.now(timezone.utc) - timedelta(days=1)

        repo.get_by_token.return_value = mock_agmt

        raised = False
        try:
            await service.get_by_token("expired-token-123")
        except AppException as exc:
            raised = True
            assert exc.status_code == 410
        assert raised, "Expected AppException with status 410"

    asyncio.run(run_test())


def test_sign_agreement_success():
    """Test full e-sign execution: PDF generation, S3 upload, user terms update, and completion email."""
    async def run_test():
        repo = AsyncMock()
        repo.db = MagicMock()
        email_service = AsyncMock()
        template_service = AsyncMock()
        template_service.render_template.return_value = "<html>Completed</html>"
        storage_service = AsyncMock()
        storage_service.upload_bytes.return_value = "agreements/uuid/file.pdf"
        storage_service.generate_presigned_url.return_value = "https://cdn.example.com/agreement.pdf"

        pdf_service = MagicMock()
        pdf_service.generate_signed_agreement_pdf.return_value = b"%PDF-1.4 Mock Executed Contract"

        service = VendorAgreementService(
            repository=repo,
            email_service=email_service,
            email_template_service=template_service,
            storage_service=storage_service,
            pdf_service=pdf_service,
        )

        mock_vendor = MagicMock()
        mock_vendor.email = "host@test.com"
        mock_vendor.full_name = "Karma Tenzin"
        mock_vendor.phone = "+919876543210"
        mock_vendor.is_terms_accepted = False
        mock_vendor.company = MagicMock(name="Tenzin Homestay", addresses=[])

        mock_agmt = MagicMock()
        mock_agmt.public_id = uuid.uuid4()
        mock_agmt.token = "valid-token-xyz"
        mock_agmt.status = AgreementStatus.VIEWED
        mock_agmt.expires_at = datetime.now(timezone.utc) + timedelta(days=2)
        mock_agmt.vendor = mock_vendor
        mock_agmt.terms_snapshot = None

        repo.get_by_token.return_value = mock_agmt

        sign_dto = SignAgreementDTO(
            signer_name="Karma Tenzin",
            signature_type="typed",
            signature_data="Karma Tenzin",
            terms_accepted=True,
            consent_acknowledged=True,
        )

        signed_agmt = await service.sign_agreement(
            token="valid-token-xyz",
            sign_dto=sign_dto,
            client_ip="203.0.113.42",
            user_agent="TestAgent/1.0",
        )

        assert signed_agmt.status == AgreementStatus.SIGNED
        assert signed_agmt.signer_name == "Karma Tenzin"
        assert signed_agmt.document_hash is not None
        assert signed_agmt.pdf_file_url is not None
        assert mock_vendor.is_terms_accepted is True
        assert storage_service.upload_bytes.called
        assert email_service.send_email.called
        assert repo.update.called

    asyncio.run(run_test())


def test_sign_agreement_already_signed_error():
    """Test that attempting to sign an already signed agreement raises 400."""
    async def run_test():
        repo = AsyncMock()
        service = VendorAgreementService(
            repository=repo,
            email_service=AsyncMock(),
            email_template_service=AsyncMock(),
            storage_service=AsyncMock(),
            pdf_service=MagicMock(),
        )

        mock_agmt = MagicMock()
        mock_agmt.token = "already-signed"
        mock_agmt.status = AgreementStatus.SIGNED
        repo.get_by_token.return_value = mock_agmt

        sign_dto = SignAgreementDTO(
            signer_name="Karma Tenzin",
            signature_type="typed",
            signature_data="Karma Tenzin",
        )

        raised = False
        try:
            await service.sign_agreement("already-signed", sign_dto)
        except AppException as exc:
            raised = True
            assert exc.status_code == 400
        assert raised, "Expected AppException with status 400"

    asyncio.run(run_test())


def test_onboard_host_dispatches_agreement():
    """Test that AdminOnboardHostUseCase triggers agreement creation when send_agreement=True."""
    async def run_test():
        created_user = MagicMock(
            id=15,
            public_id=uuid.uuid4(),
            email="newhost@example.com",
            full_name="New Host",
            phone="9876543210",
            role=UserRole.VENDOR,
            status=UserStatus.ACTIVE,
            company=None,
        )

        user_service = AsyncMock()
        user_service.get_user_by_email.return_value = None
        user_service.get_user_by_phone.return_value = None
        user_service.create_user.return_value = created_user
        user_service.get_user_by_id.return_value = created_user
        user_service.user_repository = MagicMock()
        user_service.user_repository.db = MagicMock()
        user_service.user_repository.db.flush = AsyncMock()
        user_service.build_vendor_response = AsyncMock(
            return_value=VendorUserResponseData(
                id=str(created_user.public_id),
                email=created_user.email,
                full_name=created_user.full_name,
                phone=created_user.phone,
                status="active",
                role=UserRole.VENDOR,
            )
        )

        company_service = AsyncMock()
        address_service = AsyncMock()
        event_bus = AsyncMock()
        current_user = CurrentUser(id=1, role="admin")

        agreement_service = AsyncMock()

        use_case = AdminOnboardHostUseCase(
            user_service=user_service,
            company_service=company_service,
            address_service=address_service,
            event_bus=event_bus,
            current_user=current_user,
            agreement_service=agreement_service,
        )

        dto = AdminOnboardHostDTO(
            full_name="New Host",
            email="newhost@example.com",
            phone="9876543210",
            company_name="New Homestay",
            send_agreement=True,
            commission_percentage=12.0,
            agreement_notes="Introductory rate",
        )

        response = await use_case.execute(dto)

        assert response.email == "newhost@example.com"
        assert agreement_service.create_and_send_agreement.called
        call_kwargs = agreement_service.create_and_send_agreement.call_args.kwargs
        assert call_kwargs["commission_percentage"] == 12.0
        assert call_kwargs["custom_notes"] == "Introductory rate"

    asyncio.run(run_test())


def test_agreement_pdf_with_logo_and_custom_operator_info():
    """Verify AgreementPdfService generates valid PDF with custom logo_bytes and operator_info."""
    pdf_service = AgreementPdfService()

    mock_vendor = MagicMock(full_name="Pemba Sherpa", email="pemba@example.com", phone="+919876543210")
    mock_company = MagicMock(name="Khangchendzonga Homestay")
    mock_agreement = MagicMock(
        public_id=uuid.uuid4(),
        signer_name="Pemba Sherpa",
        signer_email="pemba@example.com",
        signer_phone="+919876543210",
        commission_percentage=12.0,
        signed_at=datetime.now(timezone.utc),
        signature_type="typed",
        signature_data="Pemba Sherpa",
        document_hash="112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00",
        signer_ip="10.0.0.1",
        signer_user_agent="Mozilla/5.0 Test Agent",
    )

    # 1x1 valid PNG bytes
    tiny_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
        b"\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02"
        b"\xfe\xa7T\x81\x7f\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    custom_operator = {
        "app_name": "TashiHome Himalayan Stays",
        "tagline": "Curated Mountain Hospitality",
        "legal_name": "TashiHome Himalayan Hospitality Pvt. Ltd.",
        "address": "Tibet Road, Gangtok, Sikkim 737101",
        "email": "contact@tashihomes.in",
        "phone": "+91 98000 00000",
        "website": "www.tashihomes.in",
        "title": "HIMALAYAN HOMESTAY PARTNERSHIP CONTRACT",
    }

    pdf_bytes = pdf_service.generate_signed_agreement_pdf(
        agreement=mock_agreement,
        vendor=mock_vendor,
        company=mock_company,
        address=None,
        logo_bytes=tiny_png,
        operator_info=custom_operator,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")


def test_create_agreement_with_custom_template_from_settings():
    """Verify VendorAgreementService dynamically reads template clauses and commission from SettingService."""
    async def run_test():
        import json

        repo = AsyncMock()
        repo.create.side_effect = lambda agmt, commit=False: agmt
        email_service = AsyncMock()
        template_service = AsyncMock()
        template_service.render_template.return_value = "<html>Dynamic Invitation</html>"
        storage_service = AsyncMock()
        storage_service.get_display_url.return_value = "https://cdn.example.com/agreement-logo.png"
        pdf_service = MagicMock()

        setting_service = AsyncMock()

        custom_clauses = [
            {"heading": "1. Organic Breakfast Obligation", "body": "Hosts must provide local organic breakfast daily."},
            {"heading": "2. High Altitude Safety Protocol", "body": "Hosts must provide medical emergency contact details."},
        ]

        async def fake_get_value(key, default=None):
            settings_map = {
                "app_name": "Sikkim Homestays Network",
                "agreement_title": "Certified Homestay Operator Contract",
                "agreement_template_terms": json.dumps(custom_clauses),
                "default_commission_percentage": "14.5",
                "agreement_default_expiry_days": "10",
                "agreement_logo": "settings/agreement_logo.png",
                "contact_email": "hosts@sikkimhomestays.in",
            }
            return settings_map.get(key, default)

        setting_service.get_value.side_effect = fake_get_value

        service = VendorAgreementService(
            repository=repo,
            email_service=email_service,
            email_template_service=template_service,
            storage_service=storage_service,
            pdf_service=pdf_service,
            setting_service=setting_service,
        )

        mock_vendor = MagicMock(
            id=99,
            email="norbu@example.com",
            full_name="Norbu Lepcha",
            company=MagicMock(name="Lepcha Eco Cottage"),
        )

        agreement = await service.create_and_send_agreement(
            vendor=mock_vendor,
            custom_notes="Complimentary green tea on arrival.",
        )

        assert agreement.commission_percentage == 14.5
        assert "Certified Homestay Operator Contract" in agreement.title
        assert agreement.expires_at > datetime.now(timezone.utc) + timedelta(days=9)

        # Verify terms snapshot contains custom setting clauses + custom notes
        saved_clauses = json.loads(agreement.terms_snapshot)
        assert len(saved_clauses) == 3
        assert saved_clauses[0]["heading"] == "1. Organic Breakfast Obligation"
        assert saved_clauses[1]["heading"] == "2. High Altitude Safety Protocol"
        assert saved_clauses[2]["heading"] == "Special Terms & Annexures"
        assert "Complimentary green tea" in saved_clauses[2]["body"]

        # Verify email dispatched with setting-driven subject and template data
        assert email_service.send_email.called
        email_kwargs = email_service.send_email.call_args.kwargs
        assert "Sikkim Homestays Network" in email_kwargs["subject"]

    asyncio.run(run_test())


def test_get_public_agreement_use_case_safe_addresses():
    """Verify GetPublicAgreementUseCase safely extracts company/vendor addresses without MissingGreenlet."""
    from app.application.use_case.public.agreements.get_public_agreement_use_case import GetPublicAgreementUseCase

    async def run_test():
        agreement_service = AsyncMock()

        mock_agreement = MagicMock(
            token="test-token-safe-123",
            title="Host Partnership Agreement - Tenzin",
            version="1.0",
            status=AgreementStatus.SENT,
            commission_percentage=10.0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=5),
            terms_snapshot=None,
            signed_at=None,
        )

        mock_vendor = MagicMock(
            full_name="Tenzin Norbu",
            email="tenzin@example.com",
            phone="+919876543210",
        )
        mock_company = MagicMock()
        mock_company.name = "Tenzin Homestay"
        # Simulating address object
        mock_addr = MagicMock(
            city="Gangtok",
            address_line1="Development Area",
        )
        mock_company.addresses = [mock_addr]
        mock_vendor.company = mock_company
        mock_agreement.vendor = mock_vendor

        agreement_service.get_by_token.return_value = mock_agreement
        agreement_service.get_download_url.return_value = "https://cdn.example.com/agmt.pdf"
        agreement_service.get_operator_info.return_value = {
            "app_name": "TashiHome",
            "legal_name": "TashiHome Technologies Pvt. Ltd.",
            "logo_url": "https://cdn.example.com/logo.png",
            "address": "Gangtok, Sikkim",
        }

        use_case = GetPublicAgreementUseCase(agreement_service)
        data = await use_case.execute("test-token-safe-123")

        assert data.token == "test-token-safe-123"
        assert data.host_name == "Tenzin Norbu"
        assert data.city == "Gangtok"
        assert data.property_address == "Development Area"
        assert data.operator_name == "TashiHome"
        assert data.operator_logo_url == "https://cdn.example.com/logo.png"

    asyncio.run(run_test())


def test_email_templates_setting_driven_rendering():
    """Verify that email templates correctly render setting-driven logo, app_name, and legal details."""
    async def run_test():
        template_service = EmailTemplateService()

        # 1. Test host_agreement_invitation with custom logo
        invitation_data = {
            "app_name": "Himalayan Retreats",
            "logo_url": "https://cdn.example.com/himalayan_logo.png",
            "logo_display": "block",
            "legal_name": "Himalayan Retreats Technologies Private Limited",
            "legal_address": "Kalimpong, West Bengal, India",
            "support_email": "care@himalayanretreats.in",
            "host_name": "Dawa Sherpa",
            "company_name": "Kanchenjunga View Homestay",
            "signing_url": "https://himalayanretreats.in/agreements/tok_12345",
            "commission_percentage": "12.0",
            "expires_in_days": "7",
        }
        invitation_html = await template_service.render_template(
            "host_agreement_invitation",
            invitation_data,
            use_cache=False,
        )

        assert "Himalayan Retreats" in invitation_html
        assert "https://cdn.example.com/himalayan_logo.png" in invitation_html
        assert "display:block" in invitation_html
        assert "Dawa Sherpa" in invitation_html
        assert "Kanchenjunga View Homestay" in invitation_html
        assert "Himalayan Retreats Technologies Private Limited" in invitation_html
        assert "Kalimpong, West Bengal, India" in invitation_html
        assert "TASHIHOME" not in invitation_html

        # 2. Test host_agreement_completed with custom logo
        completed_data = {
            "app_name": "Himalayan Retreats",
            "logo_url": "https://cdn.example.com/himalayan_logo.png",
            "logo_display": "block",
            "legal_name": "Himalayan Retreats Technologies Private Limited",
            "legal_address": "Kalimpong, West Bengal, India",
            "support_email": "care@himalayanretreats.in",
            "host_name": "Dawa Sherpa",
            "company_name": "Kanchenjunga View Homestay",
            "agreement_ref": "AGMT-HIM-001",
            "signed_date": "16 Sep 2026, 14:00:00 UTC",
            "pdf_download_url": "https://cdn.example.com/signed_contract.pdf",
            "dashboard_url": "https://himalayanretreats.in/vendor",
        }
        completed_html = await template_service.render_template(
            "host_agreement_completed",
            completed_data,
            use_cache=False,
        )

        assert "Himalayan Retreats" in completed_html
        assert "https://cdn.example.com/himalayan_logo.png" in completed_html
        assert "countersigned by Himalayan Retreats" in completed_html
        assert "Himalayan Retreats Technologies Private Limited" in completed_html
        assert "TASHIHOME" not in completed_html

        # 3. Test fallback when no logo is configured
        no_logo_data = {
            **invitation_data,
            "logo_url": "",
            "logo_display": "none",
        }
        no_logo_html = await template_service.render_template(
            "host_agreement_invitation",
            no_logo_data,
            use_cache=False,
        )
        assert "display:none" in no_logo_html
        assert "Himalayan Retreats" in no_logo_html

    asyncio.run(run_test())


def test_vendor_agreement_service_email_data_setting_driven():
    """Verify that VendorAgreementService passes setting-driven branding to email templates."""
    async def run_test():
        repo = AsyncMock()
        repo.create.side_effect = lambda agmt, commit=False: agmt
        email_service = AsyncMock()
        template_service = AsyncMock()
        template_service.render_template.return_value = "<html>Setting Driven Invitation</html>"
        storage_service = AsyncMock()
        storage_service.get_display_url.return_value = "https://cdn.example.com/custom_brand_logo.png"
        pdf_service = MagicMock()

        setting_service = AsyncMock()
        async def fake_get_value(key, default=None):
            settings_map = {
                "app_name": "Mountain Stays Co",
                "agreement_company_legal_name": "Mountain Stays Pvt. Ltd.",
                "agreement_company_address": "Darjeeling, West Bengal",
                "contact_email": "partners@mountainstays.com",
                "agreement_logo": "settings/mountain_logo.png",
            }
            return settings_map.get(key, default)

        setting_service.get_value.side_effect = fake_get_value

        service = VendorAgreementService(
            repository=repo,
            email_service=email_service,
            email_template_service=template_service,
            storage_service=storage_service,
            pdf_service=pdf_service,
            setting_service=setting_service,
        )

        mock_vendor = MagicMock(
            id=10,
            email="host@mountainstays.com",
            full_name="Pemba Sherpa",
            company=MagicMock(name="Darjeeling Tea Homestay"),
        )

        await service.create_and_send_agreement(vendor=mock_vendor)

        assert template_service.render_template.called
        template_call_args = template_service.render_template.call_args
        template_name = template_call_args.args[0]
        template_data = template_call_args.args[1]

        assert template_name == "host_agreement_invitation"
        assert template_data["app_name"] == "Mountain Stays Co"
        assert template_data["logo_url"] == "https://cdn.example.com/custom_brand_logo.png"
        assert template_data["logo_display"] == "block"
        assert template_data["legal_name"] == "Mountain Stays Pvt. Ltd."
        assert template_data["legal_address"] == "Darjeeling, West Bengal"
        assert template_data["support_email"] == "partners@mountainstays.com"
        assert "year" in template_data

    asyncio.run(run_test())


def test_sign_agreement_with_authenticated_user_authorization():
    """Verify that signing with matching user succeeds, and mismatched user raises 403."""
    async def run_test():
        repo = AsyncMock()
        service = VendorAgreementService(
            repository=repo,
            email_service=AsyncMock(),
            email_template_service=AsyncMock(),
            storage_service=AsyncMock(),
            pdf_service=MagicMock(),
        )

        mock_agreement = MagicMock()
        mock_agreement.vendor_id = 42
        mock_agreement.status = AgreementStatus.VIEWED
        mock_agreement.expires_at = datetime.now(timezone.utc) + timedelta(days=2)
        mock_agreement.terms_snapshot = None
        mock_agreement.vendor = MagicMock(id=42, email="validhost@test.com")
        mock_agreement.pdf_file_url = None

        repo.get_by_token.return_value = mock_agreement

        sign_dto = SignAgreementDTO(
            signer_name="Valid Host",
            terms_accepted=True,
            consent_acknowledged=True,
            signature_type="drawn",
            signature_data="data:image/png;base64,123",
        )

        # 1. Matching host ID succeeds
        await service.sign_agreement(
            token="valid_token",
            sign_dto=sign_dto,
            authenticated_user_id=42,
            authenticated_user_role="vendor",
        )
        assert mock_agreement.status == AgreementStatus.SIGNED

        # Reset status for next test
        mock_agreement.status = AgreementStatus.VIEWED

        # 2. Mismatched host ID raises 403 SIGNER_MISMATCH
        try:
            await service.sign_agreement(
                token="valid_token",
                sign_dto=sign_dto,
                authenticated_user_id=999,  # Mismatched user
                authenticated_user_role="vendor",
            )
            assert False, "Expected 403 AppException on mismatched user"
        except AppException as exc:
            assert exc.status_code == 403
            assert exc.error_code == "SIGNER_MISMATCH"

        # 3. Admin user signing on behalf of host with different ID is rejected (host must sign)
        mock_agreement.status = AgreementStatus.VIEWED
        try:
            await service.sign_agreement(
                token="valid_token",
                sign_dto=sign_dto,
                authenticated_user_id=1,  # Admin user ID != 42
                authenticated_user_role="admin",
            )
            assert False, "Expected 403 AppException on mismatched user even if admin"
        except AppException as exc:
            assert exc.status_code == 403
            assert exc.error_code == "SIGNER_MISMATCH"

    asyncio.run(run_test())


def test_get_my_vendor_agreement_use_case():
    """Verify that GetMyVendorAgreementUseCase retrieves and formats vendor's latest agreement."""
    async def run_test():
        from app.application.use_case.vendor.agreements.get_my_agreement_use_case import (
            GetMyVendorAgreementUseCase,
        )

        service = MagicMock(spec=VendorAgreementService)
        service.repository = AsyncMock()

        mock_vendor = MagicMock()
        mock_vendor.full_name = "Tenzin Norbu"
        mock_vendor.email = "tenzin@example.com"
        mock_vendor.phone = "+919876543210"
        mock_vendor.company = MagicMock(name="Tenzin Homestay", addresses=[])

        mock_agreement = MagicMock()
        mock_agreement.public_id = uuid.uuid4()
        mock_agreement.token = "tenzin_token_123"
        mock_agreement.title = "TASHIHOME HOST PARTNERSHIP AGREEMENT"
        mock_agreement.version = "1.0"
        mock_agreement.agreement_type = AgreementType.HOST_ONBOARDING
        mock_agreement.status = AgreementStatus.SIGNED
        mock_agreement.commission_percentage = 12.5
        mock_agreement.expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        mock_agreement.signed_at = datetime.now(timezone.utc)
        mock_agreement.signer_name = "Tenzin Norbu"
        mock_agreement.signer_email = "tenzin@example.com"
        mock_agreement.signature_type = "drawn"
        mock_agreement.signature_data = "data:image/png;base64,sample"
        mock_agreement.document_hash = "abc123hash"
        mock_agreement.signer_ip = "127.0.0.1"
        mock_agreement.created_at = datetime.now(timezone.utc)
        mock_agreement.terms_snapshot = None
        mock_agreement.vendor = mock_vendor

        service.repository.get_latest_by_vendor_id.return_value = mock_agreement
        service.get_download_url = AsyncMock(return_value="https://cdn.example.com/tenzin_agreement.pdf")
        service.get_operator_info = AsyncMock(return_value={
            "app_name": "TashiHome",
            "legal_name": "TashiHome Platforms Pvt Ltd",
            "logo_url": "https://cdn.example.com/logo.png",
            "address": "Gangtok, Sikkim",
        })

        use_case = GetMyVendorAgreementUseCase(agreement_service=service)

        mock_user = MagicMock()
        mock_user.id = 55

        result = await use_case.execute(current_user=mock_user)

        assert result is not None
        assert result.token == "tenzin_token_123"
        assert result.host_name == "Tenzin Norbu"
        assert result.host_email == "tenzin@example.com"
        assert result.commission_percentage == 12.5
        assert result.status == "signed"
        assert result.signature_type == "drawn"
        assert result.signature_data == "data:image/png;base64,sample"
        assert result.pdf_download_url == "https://cdn.example.com/tenzin_agreement.pdf"

    asyncio.run(run_test())


def test_sign_agreement_email_uses_preview_url():
    """Verify that sign_agreement passes the web preview URL instead of raw S3 presigned URL to the completion email."""
    async def run_test():
        repo = AsyncMock()
        email_service = AsyncMock()
        template_service = AsyncMock()
        template_service.render_template.return_value = "<html>Completed Email</html>"
        storage_service = AsyncMock()
        storage_service.upload_bytes.return_value = "agreements/file.pdf"
        storage_service.generate_presigned_url.return_value = "https://s3.amazonaws.com/bucket/raw_s3_link.pdf"

        pdf_service = MagicMock()
        pdf_service.generate_signed_agreement_pdf.return_value = b"%PDF-1.4 Data"

        service = VendorAgreementService(
            repository=repo,
            email_service=email_service,
            email_template_service=template_service,
            storage_service=storage_service,
            pdf_service=pdf_service,
        )

        mock_vendor = MagicMock()
        mock_vendor.email = "host@secure.com"
        mock_vendor.full_name = "Secure Host"

        mock_agmt = MagicMock()
        mock_agmt.public_id = uuid.uuid4()
        mock_agmt.token = "secure-token-abc"
        mock_agmt.status = AgreementStatus.VIEWED
        mock_agmt.expires_at = datetime.now(timezone.utc) + timedelta(days=5)
        mock_agmt.vendor = mock_vendor
        mock_agmt.terms_snapshot = None

        repo.get_by_token.return_value = mock_agmt

        sign_dto = SignAgreementDTO(
            signer_name="Secure Host",
            signature_type="typed",
            signature_data="Secure Host",
            terms_accepted=True,
            consent_acknowledged=True,
        )

        await service.sign_agreement(
            token="secure-token-abc",
            sign_dto=sign_dto,
        )

        # Check the template_data passed into template_service.render_template
        render_call_args = template_service.render_template.call_args
        assert render_call_args is not None
        template_data = render_call_args[0][1]

        # The email link MUST point to the host dashboard agreement preview, NOT the raw S3 link
        assert "s3.amazonaws.com" not in template_data["agreement_view_url"]
        assert "/vendor/agreements" in template_data["agreement_view_url"]
        assert "s3.amazonaws.com" not in template_data["pdf_download_url"]
        assert "/vendor/agreements" in template_data["pdf_download_url"]

    asyncio.run(run_test())


def test_agreement_email_dispatched_via_event_bus():
    """Verify agreement invitation and completion emails emit domain events to the event bus."""
    async def run_test():
        repo = AsyncMock()
        email_service = AsyncMock()
        template_service = AsyncMock()
        storage_service = AsyncMock()
        pdf_service = MagicMock()
        pdf_service.generate_signed_agreement_pdf.return_value = b"%PDF-1.4 Data"
        event_bus = AsyncMock()

        service = VendorAgreementService(
            repository=repo,
            email_service=email_service,
            email_template_service=template_service,
            storage_service=storage_service,
            pdf_service=pdf_service,
            event_bus=event_bus,
        )

        vendor = User(
            id=42,
            email="event_host@example.com",
            full_name="Event Host",
            phone="+919876543210",
        )

        repo.create.side_effect = lambda ag, commit=True: ag
        repo.update.side_effect = lambda ag: ag

        # 1. Create and send agreement -> should publish AgreementInvitationSentEvent
        created = await service.create_and_send_agreement(vendor=vendor)
        assert created.first_party_signed_at is not None
        assert created.status == AgreementStatus.SENT

        assert event_bus.publish.call_count == 1
        invitation_event = event_bus.publish.call_args[0][0]
        assert invitation_event.name == "agreement.invitation_sent"
        assert invitation_event.payload["recipient_email"] == "event_host@example.com"
        assert invitation_event.payload["token"] == created.token

        # 2. Host signs agreement -> should publish AgreementCompletedEvent and set status to SIGNED
        repo.get_by_token.return_value = created
        sign_dto = SignAgreementDTO(
            signer_name="Event Host",
            signature_type="drawn",
            signature_data="data:image/png;base64,drawndata",
            terms_accepted=True,
            consent_acknowledged=True,
        )
        signed = await service.sign_agreement(token=created.token, sign_dto=sign_dto)
        assert signed.status == AgreementStatus.SIGNED
        assert signed.is_bilateral_signed is True
        assert signed.first_party_signer_name is not None
        assert signed.signer_name == "Event Host"

        assert event_bus.publish.call_count == 2
        completed_event = event_bus.publish.call_args[0][0]
        assert completed_event.name == "agreement.completed"
        assert completed_event.payload["signer_name"] == "Event Host"
        assert completed_event.payload["signer_email"] == "event_host@example.com"

    asyncio.run(run_test())


def test_bilateral_signatures_and_countersign():
    """Verify bilateral signature flow: partially_signed when first party pending, and countersign completing it."""
    async def run_test():
        repo = AsyncMock()
        email_service = AsyncMock()
        template_service = AsyncMock()
        storage_service = AsyncMock()
        pdf_service = MagicMock()
        pdf_service.generate_signed_agreement_pdf.return_value = b"%PDF-1.4 Data"
        event_bus = AsyncMock()

        service = VendorAgreementService(
            repository=repo,
            email_service=email_service,
            email_template_service=template_service,
            storage_service=storage_service,
            pdf_service=pdf_service,
            event_bus=event_bus,
        )

        mock_vendor = MagicMock()
        mock_vendor.id = 99
        mock_vendor.email = "pending_host@example.com"
        mock_vendor.full_name = "Pending Host"

        # Agreement where First Party has NOT signed yet
        agmt = VendorAgreement(
            id=101,
            public_id=uuid.uuid4(),
            token="unilateral_token",
            status=AgreementStatus.VIEWED,
            commission_percentage=10.0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=5),
            vendor_id=99,
            first_party_signed_at=None,
        )
        agmt.vendor = mock_vendor
        repo.get_by_token.return_value = agmt
        repo.get_by_public_id.return_value = agmt
        repo.update.side_effect = lambda a: a

        # Host signs first -> status should transition to PARTIALLY_SIGNED
        sign_dto = SignAgreementDTO(
            signer_name="Pending Host",
            signature_type="typed",
            signature_data="Pending Host",
            terms_accepted=True,
            consent_acknowledged=True,
        )
        partially_signed = await service.sign_agreement("unilateral_token", sign_dto)
        assert partially_signed.status == AgreementStatus.PARTIALLY_SIGNED
        assert partially_signed.is_first_party_signed is False
        assert partially_signed.is_second_party_signed is True
        assert partially_signed.is_bilateral_signed is False

        # Admin countersigns -> status should now become SIGNED
        mock_admin = MagicMock()
        mock_admin.full_name = "Admin Operations Lead"

        from app.application.dto.agreements.agreement_dto import AdminCountersignAgreementDTO
        countersign_dto = AdminCountersignAgreementDTO(
            signer_name="Admin Operations Lead",
            signer_role="Operations Director",
            signature_type="digital",
        )
        fully_signed = await service.countersign_agreement(
            agreement_id=agmt.public_id,
            admin_user=mock_admin,
            data=countersign_dto,
        )
        assert fully_signed.status == AgreementStatus.SIGNED
        assert fully_signed.is_bilateral_signed is True
        assert fully_signed.first_party_signer_name == "Admin Operations Lead"
        assert fully_signed.first_party_signer_role == "Operations Director"

    asyncio.run(run_test())


def test_agreement_event_handlers_execution(monkeypatch):
    """Verify AgreementInvitationSentHandler and AgreementCompletedHandler process events and invoke email service."""
    async def run_test():
        from app.events.handles.agreements.agreement_invitation_sent_handler import AgreementInvitationSentHandler
        from app.events.handles.agreements.agreement_completed_handler import AgreementCompletedHandler

        mock_email_svc = AsyncMock()
        mock_template_svc = AsyncMock()
        mock_template_svc.render_template.return_value = "<html>Rendered Content</html>"
        mock_storage_svc = AsyncMock()
        mock_storage_svc.get_display_url.return_value = "https://cdn.example.com/logo.png"
        mock_storage_svc.download_bytes.return_value = b"%PDF-Executed"

        # Mock dependencies in handler modules
        from unittest.mock import patch
        with patch("app.events.handles.agreements.agreement_invitation_sent_handler.get_email_service", return_value=mock_email_svc), \
             patch("app.events.handles.agreements.agreement_invitation_sent_handler.get_email_template_service", return_value=mock_template_svc), \
             patch("app.events.handles.agreements.agreement_invitation_sent_handler.get_storage_service", return_value=mock_storage_svc), \
             patch("app.events.handles.agreements.agreement_completed_handler.get_email_service", return_value=mock_email_svc), \
             patch("app.events.handles.agreements.agreement_completed_handler.get_email_template_service", return_value=mock_template_svc), \
             patch("app.events.handles.agreements.agreement_completed_handler.get_storage_service", return_value=mock_storage_svc):

            # 1. Test AgreementInvitationSentHandler
            invitation_payload = {
                "recipient_name": "Handler Host",
                "recipient_email": "handler_host@example.com",
                "token": "tok-12345",
                "commission_percentage": 15.0,
            }
            await AgreementInvitationSentHandler.handle(invitation_payload)
            assert mock_email_svc.send_email.call_count == 1
            call_kwargs = mock_email_svc.send_email.call_args[1]
            assert call_kwargs["to_email"] == "handler_host@example.com"
            assert "Host Partnership Agreement" in call_kwargs["subject"]

            # 2. Test AgreementCompletedHandler
            completed_payload = {
                "signer_name": "Handler Host",
                "signer_email": "handler_host@example.com",
                "token": "tok-12345",
                "public_id": "00000000-0000-0000-0000-000000000001",
                "pdf_file_url": "agreements/doc.pdf",
            }
            await AgreementCompletedHandler.handle(completed_payload)
            assert mock_email_svc.send_email.call_count == 2
            completed_call_kwargs = mock_email_svc.send_email.call_args[1]
            assert completed_call_kwargs["to_email"] == "handler_host@example.com"
            assert "Executed Copy" in completed_call_kwargs["subject"]
            assert len(completed_call_kwargs["attachments"]) == 1

    asyncio.run(run_test())








