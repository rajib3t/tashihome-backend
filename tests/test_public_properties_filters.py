import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.application.dto.properties.public.property import PublicPropertyQueryDTO
from app.application.dto.stays.public.stay import PublicSearchStaysQueryDTO
from app.application.use_case.public.property.get_properties_use_case import PublicPropertiesUseCase
from app.core.exceptions import AppException
from app.models.property_model import Property, PropertyStatus, PropertyType
from app.models.city_model import City
from app.models.location_model import Location
from app.repositories.base_repository import Page


def test_public_property_dto_slugs_and_price_filters():
    # Valid DTO with slugs and price range
    dto = PublicPropertyQueryDTO(
        city_slug="manali",
        location_slug="old-manali",
        country_slug="india",
        min_price=1000.0,
        max_price=5000.0,
        sort_by="name",
        sort_order="asc",
        is_featured=True,
    )
    assert dto.city_slug == "manali"
    assert dto.location_slug == "old-manali"
    assert dto.country_slug == "india"
    assert dto.min_price == 1000.0
    assert dto.max_price == 5000.0
    assert dto.sort_by == "name"
    assert dto.sort_order == "asc"
    assert dto.is_featured is True

    # Valid DTO with sort_by="price"
    dto_price = PublicPropertyQueryDTO(
        sort_by="price",
        sort_order="desc",
    )
    assert dto_price.sort_by == "price"
    assert dto_price.sort_order == "desc"

    # Invalid sort_by
    with pytest.raises(AppException) as exc_info:
        PublicPropertyQueryDTO(sort_by="invalid_field")
    assert exc_info.value.detail.get("error_code") == "INVALID_SORT_BY"

    # Invalid negative price
    with pytest.raises(AppException) as exc_info:
        PublicPropertyQueryDTO(min_price=-100.0)
    assert exc_info.value.detail.get("error_code") == "INVALID_PRICE"

    # Invalid price range (min_price > max_price)
    with pytest.raises(AppException) as exc_info:
        PublicPropertyQueryDTO(min_price=5000.0, max_price=1000.0)
    assert exc_info.value.detail.get("error_code") == "INVALID_PRICE_RANGE"


def test_public_search_stays_dto_slugs():
    dto = PublicSearchStaysQueryDTO(
        city_slug="manali",
        location_slug="old-manali",
        country_slug="india",
    )
    assert dto.city_slug == "manali"
    assert dto.location_slug == "old-manali"
    assert dto.country_slug == "india"


def test_public_properties_use_case_execution():
    async def run_test():
        property_service = AsyncMock()
        storage_service = AsyncMock()
        storage_service.generate_presigned_url = AsyncMock(return_value="https://cdn.example.com/asset.jpg")
        city_service = AsyncMock()
        location_service = AsyncMock()

        # Mock city and location by slug
        mock_city = MagicMock(spec=City)
        mock_city.id = 1
        mock_city.public_id = "city-uuid-1"
        mock_city.name = "Manali"
        mock_city.slug = "manali"
        city_service.get_by_slug.return_value = mock_city

        mock_location = MagicMock(spec=Location)
        mock_location.id = 10
        mock_location.public_id = "loc-uuid-1"
        mock_location.name = "Old Manali"
        mock_location.slug = "old-manali"
        location_service.get_by_slug.return_value = mock_location

        # Mock properties
        prop1 = MagicMock(spec=Property)
        prop1.id = 1
        prop1.public_id = "prop-1"
        prop1.name = "Alpha Resort"
        prop1.slug = "alpha-resort"
        prop1.currency = "INR"
        prop1.type = PropertyType.COTTAGE
        prop1.price_per_night = 3000.0
        prop1.sale_per_night = 2500.0
        prop1.is_featured = True
        prop1.status = PropertyStatus.ACTIVE
        prop1.address = "Old Manali Rd"
        prop1.city = mock_city
        prop1.location = mock_location
        prop1.property_assets = []
        prop1.tags = []
        prop1.rooms = []
        prop1.property_category = None
        prop1.host = None
        prop1.latitude = None
        prop1.longitude = None
        prop1.description = "Nice cottage"

        fake_page = Page(items=[prop1], total=1, page=1, page_size=10)
        property_service.search_stays.return_value = fake_page

        use_case = PublicPropertiesUseCase(
            property_service=property_service,
            storage_service=storage_service,
            city_service=city_service,
            location_service=location_service,
        )

        dto = PublicPropertyQueryDTO(
            city_slug="manali",
            location_slug="old-manali",
            country_slug="india",
            min_price=1000.0,
            max_price=4000.0,
            sort_by="name",
            sort_order="asc",
        )

        result_page = await use_case.execute(dto)

        assert result_page.total == 1
        assert len(result_page.items) == 1
        item = result_page.items[0]
        assert item["name"] == "Alpha Resort"
        assert item["city"]["slug"] == "manali"
        assert item["location"]["slug"] == "old-manali"

        property_service.search_stays.assert_called_once()
        call_kwargs = property_service.search_stays.call_args.kwargs
        assert call_kwargs["city_slug"] == "manali"
        assert call_kwargs["location_slug"] == "old-manali"
        assert call_kwargs["country_slug"] == "india"
        assert call_kwargs["min_price"] == 1000.0
        assert call_kwargs["max_price"] == 4000.0
        assert call_kwargs["sort_by"] == "name"
        assert call_kwargs["sort_order"] == "asc"

    asyncio.run(run_test())


def test_public_properties_use_case_invalid_slugs():
    async def run_test():
        property_service = AsyncMock()
        storage_service = AsyncMock()
        city_service = AsyncMock()
        location_service = AsyncMock()

        city_service.get_by_slug.return_value = None
        location_service.get_by_slug.return_value = None

        use_case = PublicPropertiesUseCase(
            property_service=property_service,
            storage_service=storage_service,
            city_service=city_service,
            location_service=location_service,
        )

        # Invalid city slug
        dto_invalid_city = PublicPropertyQueryDTO(city_slug="non-existent-city")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto_invalid_city)
        assert exc_info.value.detail.get("error_code") == "CITY_NOT_FOUND"

        # Invalid location slug
        dto_invalid_loc = PublicPropertyQueryDTO(location_slug="non-existent-loc")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto_invalid_loc)
        assert exc_info.value.detail.get("error_code") == "LOCATION_NOT_FOUND"

    asyncio.run(run_test())

