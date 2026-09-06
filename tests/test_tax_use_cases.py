import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.application.dto.tax import TaxCreateDTO, TaxQueryDTO, TaxStatusUpdateDTO, TaxUpdateDTO
from app.application.use_case.admin.tax.create_tax_use_case import CreateTaxUseCase
from app.application.use_case.admin.tax.delete_tax_use_case import DeleteTaxUseCase
from app.application.use_case.admin.tax.get_tax_use_case import GetTaxUseCase, ListTaxesUseCase
from app.application.use_case.admin.tax.update_tax_use_case import UpdateTaxStatusUseCase, UpdateTaxUseCase
from app.application.use_case.public.tax.get_public_taxes_use_case import GetDefaultTaxUseCase, GetPublicTaxesUseCase
from app.core.exceptions import AppException
from app.models.tax_model import Tax, TaxStatus, TaxType
from app.models.user_model import User, UserRole


@pytest.fixture
def mock_admin_user():
    return User(
        id=1,
        public_id=uuid4(),
        email="admin@tashihomes.in",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_tax_service():
    return MagicMock()


@pytest.mark.asyncio
async def test_create_tax_success(mock_tax_service, mock_admin_user):
    mock_tax_service.get_by_code = AsyncMock(return_value=None)
    mock_tax_service.create_tax = AsyncMock(
        side_effect=lambda tax, commit: tax
    )

    use_case = CreateTaxUseCase(mock_tax_service, mock_admin_user)
    dto = TaxCreateDTO(
        name="GST 12%",
        code="gst_12",
        rate=12.0,
        tax_type=TaxType.PERCENTAGE,
        is_inclusive=False,
        is_default=True,
        gst_number="27ABCDE1234F1Z5",
        legal_name="Tashi Homes Hospitality",
        hsn_sac_code="996311",
        cgst_rate=6.0,
        sgst_rate=6.0,
        igst_rate=12.0,
    )

    tax = await use_case.execute(dto)

    assert tax.name == "GST 12%"
    assert tax.code == "GST_12"
    assert tax.rate == 12.0
    assert tax.is_default is True
    assert tax.gst_number == "27ABCDE1234F1Z5"
    assert tax.cgst_rate == 6.0
    assert tax.created_by == 1


@pytest.mark.asyncio
async def test_create_tax_duplicate_code(mock_tax_service, mock_admin_user):
    existing = Tax(id=1, code="GST_18", name="GST 18%")
    mock_tax_service.get_by_code = AsyncMock(return_value=existing)

    use_case = CreateTaxUseCase(mock_tax_service, mock_admin_user)
    dto = TaxCreateDTO(
        name="Duplicate GST",
        code="GST_18",
        rate=18.0,
    )

    with pytest.raises(AppException) as exc_info:
        await use_case.execute(dto)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail.get("error_code") == "TAX_CODE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_get_tax_by_identifier(mock_tax_service):
    tax_obj = Tax(id=1, public_id=uuid4(), code="GST_12", name="GST 12%", rate=12.0)
    mock_tax_service.get_by_identifier = AsyncMock(return_value=tax_obj)

    use_case = GetTaxUseCase(mock_tax_service)
    result = await use_case.execute("GST_12")

    assert result.code == "GST_12"
    assert result.rate == 12.0


@pytest.mark.asyncio
async def test_update_tax_success(mock_tax_service, mock_admin_user):
    tax_obj = Tax(id=1, public_id=uuid4(), code="GST_12", name="Old GST", rate=12.0, status=TaxStatus.ACTIVE)
    mock_tax_service.get_by_identifier = AsyncMock(return_value=tax_obj)
    mock_tax_service.get_by_code = AsyncMock(return_value=None)
    mock_tax_service.update_tax = AsyncMock(side_effect=lambda tax, commit: tax)

    use_case = UpdateTaxUseCase(mock_tax_service, mock_admin_user)
    dto = TaxUpdateDTO(
        name="Updated GST 12%",
        rate=12.5,
        is_inclusive=True,
    )

    updated = await use_case.execute(str(tax_obj.public_id), dto)
    assert updated.name == "Updated GST 12%"
    assert updated.rate == 12.5
    assert updated.is_inclusive is True
    assert updated.updated_by == 1


@pytest.mark.asyncio
async def test_update_tax_status_and_delete(mock_tax_service, mock_admin_user):
    tax_obj = Tax(id=1, public_id=uuid4(), code="GST_12", status=TaxStatus.ACTIVE)
    mock_tax_service.get_by_identifier = AsyncMock(return_value=tax_obj)
    mock_tax_service.update_tax = AsyncMock(side_effect=lambda tax, commit: tax)
    mock_tax_service.delete_tax = AsyncMock()

    status_use_case = UpdateTaxStatusUseCase(mock_tax_service, mock_admin_user)
    res = await status_use_case.execute("GST_12", TaxStatus.INACTIVE)
    assert res.status == TaxStatus.INACTIVE

    delete_use_case = DeleteTaxUseCase(mock_tax_service, mock_admin_user)
    await delete_use_case.execute("GST_12", hard_delete=False)
    assert tax_obj.status == TaxStatus.INACTIVE


@pytest.mark.asyncio
async def test_public_tax_use_cases(mock_tax_service):
    taxes = [
        Tax(id=1, code="GST_12", rate=12.0, is_default=True, status=TaxStatus.ACTIVE),
        Tax(id=2, code="GST_18", rate=18.0, is_default=False, status=TaxStatus.ACTIVE),
    ]
    mock_tax_service.get_active_taxes = AsyncMock(return_value=taxes)
    mock_tax_service.get_default_tax = AsyncMock(return_value=taxes[0])

    public_list = await GetPublicTaxesUseCase(mock_tax_service).execute()
    assert len(public_list) == 2

    default_tax = await GetDefaultTaxUseCase(mock_tax_service).execute()
    assert default_tax.code == "GST_12"
    assert default_tax.is_default is True


def test_booking_service_pricing_quote_tax_exclusive():
    from datetime import date
    from app.models.property_model import Property
    from app.services.booking_service import BookingService

    service = BookingService(
        booking_repository=MagicMock(),
        room_block_repository=MagicMock(),
        property_room_type_repository=MagicMock(),
    )

    prop = Property(id=1, price_per_night=1000.0, sale_per_night=0.0, currency="INR")
    quote = service.calculate_pricing_quote(
        property_=prop,
        check_in_date=date(2026, 9, 10),
        check_out_date=date(2026, 9, 12),
        num_rooms=1,
        num_guests=2,
        tax_rate=12.0,
        is_tax_inclusive=False,
        tax_name="GST 12%",
        tax_code="GST_12",
    )

    # 2 nights * 1000 = 2000 base
    # Exclusive tax: 2000 * 0.12 = 240
    # Total: 2240
    assert quote["nights"] == 2
    assert quote["base_amount"] == 2000.0
    assert quote["tax_amount"] == 240.0
    assert quote["tax_rate"] == 12.0
    assert quote["is_tax_inclusive"] is False
    assert quote["total_amount"] == 2240.0
    assert quote["tax_name"] == "GST 12%"
    assert quote["tax_code"] == "GST_12"


def test_booking_service_pricing_quote_tax_inclusive():
    from datetime import date
    from app.models.property_model import Property
    from app.services.booking_service import BookingService

    service = BookingService(
        booking_repository=MagicMock(),
        room_block_repository=MagicMock(),
        property_room_type_repository=MagicMock(),
    )

    prop = Property(id=1, price_per_night=1120.0, sale_per_night=0.0, currency="INR")
    quote = service.calculate_pricing_quote(
        property_=prop,
        check_in_date=date(2026, 9, 10),
        check_out_date=date(2026, 9, 11),
        num_rooms=1,
        num_guests=2,
        tax_rate=12.0,
        is_tax_inclusive=True,
        tax_name="GST 12%",
        tax_code="GST_12",
    )

    # 1 night * 1120 = 1120 gross
    # Inclusive net base: 1120 / 1.12 = 1000.0
    # Inclusive tax: 1120 - 1000 = 120.0
    # Total: 1120.0
    assert quote["nights"] == 1
    assert quote["base_amount"] == 1120.0
    assert quote["tax_amount"] == 120.0
    assert quote["tax_rate"] == 12.0
    assert quote["is_tax_inclusive"] is True
    assert quote["total_amount"] == 1120.0


def test_invoice_service_generate_pdf_with_gst_details():
    from app.services.invoice_service import InvoiceService

    service = InvoiceService()
    booking_data = {
        "app_name": "Tashi Homes",
        "legal_name": "Tashi Homes Hospitality Private Limited",
        "gst_number": "27ABCDE1234F1Z5",
        "company_address": "MG Road, Gangtok, Sikkim 737101",
        "contact_email": "billing@tashihomes.in",
        "contact_phone": "+91 9876543210",
        "hsn_sac_code": "996311",
        "invoice_number": "INV-20260907-001",
        "booking_reference": "BK-20260907-99",
        "guest_name": "John Doe",
        "guest_email": "john@example.com",
        "guest_phone": "+91 9123456789",
        "property_name": "Mountain View Homestay",
        "property_address": "Upper Sichey, Gangtok, Sikkim",
        "room_type_name": "Deluxe Mountain View",
        "check_in_date": "2026-09-10",
        "check_out_date": "2026-09-12",
        "num_rooms": 1,
        "num_guests": 2,
        "price_per_night": 2000.0,
        "discount_amount": 0.0,
        "tax_amount": 480.0,
        "total_amount": 4480.0,
        "tax_rate": 12.0,
        "cgst_rate": 6.0,
        "sgst_rate": 6.0,
        "is_tax_inclusive": False,
        "currency": "INR",
    }

    pdf_bytes = service.generate_pdf(booking_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_format_booking_date_and_amount_to_words():
    from app.services.invoice_service import format_booking_date, _amount_to_words

    # Date formatting test with different formats
    assert format_booking_date("2026-09-10", "DD/MM/YYYY") == "10/09/2026"
    assert format_booking_date("2026-09-10", "YYYY-MM-DD") == "2026-09-10"
    assert format_booking_date("2026-09-10", "DD MMM YYYY") == "10 Sep 2026"
    assert format_booking_date(None, "DD/MM/YYYY") == ""

    # Amount to words test
    words = _amount_to_words(4480.0, "INR")
    assert words == "Four Thousand Four Hundred Eighty Rupees Only"

    words_lakh = _amount_to_words(125000.0, "INR")
    assert words_lakh == "One Lakh Twenty Five Thousand Rupees Only"


def test_booking_completed_event_safe_attribute_access():
    from datetime import date
    from uuid import uuid4
    from app.events.events.bookings.booking_completed_event import BookingCompletedEvent
    from app.models.booking_model import Booking, BookingStatus, PaymentStatus

    # Create dummy unattached booking
    booking = Booking(
        id=101,
        public_id=uuid4(),
        booking_reference="BK-TEST-12345",
        invoice_number="INV-20260907-001",
        guest_id=1,
        property_id=2,
        check_in_date=date(2026, 9, 10),
        check_out_date=date(2026, 9, 12),
        num_guests=2,
        num_rooms=1,
        price_per_night=2000.0,
        discount_amount=0.0,
        tax_amount=480.0,
        total_amount=4480.0,
        currency="INR",
        status=BookingStatus.CONFIRMED,
        payment_status=PaymentStatus.PAID,
    )

    event = BookingCompletedEvent(booking)
    assert event.name == "booking.completed"
    assert event.payload["booking_id"] == 101
    assert event.payload["booking_reference"] == "BK-TEST-12345"
    assert event.payload["total_amount"] == 4480.0





