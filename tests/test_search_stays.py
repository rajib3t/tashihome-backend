import asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.application.dto.stays.public.stay import PublicSearchStaysQueryDTO
from app.application.use_case.public.stay.search_stays_use_case import PublicSearchStaysUseCase
from app.core.exceptions import AppException
from app.models.property_model import Property, PropertyStatus, PropertyType
from app.repositories.base_repository import Page


def test_search_stays_dto_validations():
    # 1. Valid DTO with region / city name / dates / guests
    today = date.today()
    tomorrow = today + timedelta(days=1)
    dto = PublicSearchStaysQueryDTO(
        region="Any hill state",
        city_name="Manali",
        location_name="Old Manali",
        check_in_date=today,
        check_out_date=tomorrow,
        guests=2,
        rooms=1,
        min_price=1000.0,
        max_price=5000.0,
    )
    assert dto.region == "Any hill state"
    assert dto.city_name == "Manali"
    assert dto.location_name == "Old Manali"
    assert dto.guests == 2
    assert dto.rooms == 1

    # 2. Invalid pagination
    with pytest.raises(AppException) as exc_info:
        PublicSearchStaysQueryDTO(page=0)
    assert exc_info.value.detail.get("error_code") == "PAGINATION_INVALID"

    # 3. Invalid negative price
    with pytest.raises(AppException) as exc_info:
        PublicSearchStaysQueryDTO(min_price=-50.0)
    assert exc_info.value.detail.get("error_code") == "INVALID_PRICE"


def test_search_stays_use_case_date_validation():
    async def run_test():
        property_service = AsyncMock()
        storage_service = MagicMock()
        city_service = AsyncMock()
        location_service = AsyncMock()

        use_case = PublicSearchStaysUseCase(
            property_service=property_service,
            storage_service=storage_service,
            city_service=city_service,
            location_service=location_service,
        )

        today = date.today()
        yesterday = today - timedelta(days=1)

        # check_in provided without check_out
        dto_missing_out = PublicSearchStaysQueryDTO(check_in_date=today)
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto_missing_out)
        assert exc_info.value.detail.get("error_code") == "DATE_RANGE_REQUIRED"

        # check_out <= check_in
        dto_invalid_range = PublicSearchStaysQueryDTO(
            check_in_date=today,
            check_out_date=yesterday,
        )
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto_invalid_range)
        assert exc_info.value.detail.get("error_code") == "INVALID_DATE_RANGE"

    asyncio.run(run_test())


def test_search_stays_use_case_execution():
    async def run_test():
        property_service = AsyncMock()
        storage_service = AsyncMock()
        storage_service.generate_presigned_url = AsyncMock(return_value="https://cdn.example.com/asset.jpg")
        city_service = AsyncMock()
        location_service = AsyncMock()

        # Mock property item in page
        prop = MagicMock(spec=Property)
        prop.id = 1
        prop.public_id = "11111111-1111-1111-1111-111111111111"
        prop.name = "Mountain View Cottage"
        prop.slug = "mountain-view-cottage"
        prop.currency = "INR"
        prop.type = PropertyType.COTTAGE
        prop.price_per_night = 2500.0
        prop.sale_per_night = 2200.0
        prop.address = "Club House Road, Old Manali"
        prop.latitude = 32.24
        prop.longitude = 77.18
        prop.description = "Cozy cottage in the hills"
        prop.status = PropertyStatus.ACTIVE
        prop.location = MagicMock(public_id="22222222-2222-2222-2222-222222222222", name="Old Manali")
        prop.city = MagicMock(public_id="33333333-3333-3333-3333-333333333333", name="Manali")
        prop.property_assets = []

        fake_page = Page(items=[prop], total=1, page=1, page_size=10)
        property_service.search_stays.return_value = fake_page

        use_case = PublicSearchStaysUseCase(
            property_service=property_service,
            storage_service=storage_service,
            city_service=city_service,
            location_service=location_service,
        )

        today = date.today()
        tomorrow = today + timedelta(days=2)

        dto = PublicSearchStaysQueryDTO(
            region="Manali",
            city="Manali",
            location="Old Manali",
            check_in_date=today,
            check_out_date=tomorrow,
            adults=2,
            children=1,
            rooms=1,
        )

        result_page = await use_case.execute(dto)

        assert result_page.total == 1
        assert len(result_page.items) == 1
        item = result_page.items[0]
        assert item["name"] == "Mountain View Cottage"
        assert item["city"]["name"] == "Manali"
        assert item["location"]["name"] == "Old Manali"
        assert item["sale_per_night"] == 2200.0

        # Verify property_service.search_stays was called with parsed guests (2 + 1 = 3)
        property_service.search_stays.assert_called_once()
        call_kwargs = property_service.search_stays.call_args.kwargs
        assert call_kwargs["city_name"] == "Manali"
        assert call_kwargs["location_name"] == "Old Manali"
        assert call_kwargs["guests"] == 3
        assert call_kwargs["rooms"] == 1
        assert call_kwargs["check_in_date"] == today
        assert call_kwargs["check_out_date"] == tomorrow

        # Also test with UUID city_id
        dto_uuid = PublicSearchStaysQueryDTO(
            city_id="e0eb5d26-e005-4190-9b63-2c3a0651b9c8",
            location_id="11111111-2222-3333-4444-555555555555",
            check_in_date=today,
            check_out_date=tomorrow,
            guests=2,
        )
        res_uuid = await use_case.execute(dto_uuid)
        assert len(res_uuid.items) == 1
        call_kwargs_uuid = property_service.search_stays.call_args.kwargs
        assert call_kwargs_uuid["city_id"] == "e0eb5d26-e005-4190-9b63-2c3a0651b9c8"
        assert call_kwargs_uuid["location_id"] == "11111111-2222-3333-4444-555555555555"

    asyncio.run(run_test())

