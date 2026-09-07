import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import AppException
from app.utils.slug import generate_slug, generate_unique_slug
from app.models.country_model import Country
from app.models.city_model import City
from app.models.location_model import Location
from app.schemas.country_schema import CountrySchema
from app.schemas.city_schema import CitySchema
from app.schemas.location_schema import LocationSchema, CityLocationSchema
from app.application.dto.locations.country import CountryDTO
from app.application.dto.locations.city import CityDTO
from app.application.dto.locations.location import LocationDTO, UpdateLocationDTO
from app.application.use_case.admin.locations.country.create_country_use_case import CreateCountryUseCase
from app.application.use_case.admin.locations.country.update_country_use_case import UpdateCountryUseCase
from app.application.use_case.admin.locations.city.create_city_use_case import CreateCityUseCase
from app.application.use_case.admin.locations.city.update_city_use_case import UpdateCityUseCase
from app.application.use_case.admin.locations.location.create_location_use_case import CreateLocationUseCase
from app.application.use_case.admin.locations.location.update_location_use_case import UpdateLocationUseCase


def test_generate_unique_slug_helper():
    async def run_test():
        existing_slugs = {"test-city", "test-city-2", "test-city-3"}

        async def check_exists(slug: str) -> bool:
            return slug in existing_slugs

        # When slug doesn't exist
        unique_new = await generate_unique_slug("unique-city", check_exists)
        assert unique_new == "unique-city"

        # When slug and suffixes exist
        unique_existing = await generate_unique_slug("test-city", check_exists)
        assert unique_existing == "test-city-4"

    asyncio.run(run_test())


def test_country_slug_creation_and_uniqueness():
    async def run_test():
        country_service = AsyncMock()
        country_service.get_by_name.return_value = None
        country_service.get_by_code.return_value = None

        # Existing slugs in DB
        async def mock_get_by_slug(slug, **kwargs):
            if slug in ("india", "india-2"):
                m = MagicMock(spec=Country)
                m.id = 1
                m.slug = slug
                return m
            return None

        country_service.get_by_slug.side_effect = mock_get_by_slug
        country_service.create_country.side_effect = lambda c, **kwargs: c

        current_user = MagicMock(id=10)
        use_case = CreateCountryUseCase(country_service=country_service, current_user=current_user)

        # 1. Automatic unique slug generation (india -> india-3)
        dto = CountryDTO(name="India", code="IN")
        created = await use_case.execute(dto)
        assert created.slug == "india-3"
        assert created.name == "India"
        assert created.code == "IN"

        # 2. Custom slug generation
        dto_custom = CountryDTO(name="Republic of India", code="IND", slug="india-custom")
        created_custom = await use_case.execute(dto_custom)
        assert created_custom.slug == "india-custom"

    asyncio.run(run_test())


def test_country_slug_update():
    async def run_test():
        country_service = AsyncMock()
        existing_country = MagicMock(spec=Country)
        existing_country.id = 1
        existing_country.name = "Old Country"
        existing_country.code = "OC"
        existing_country.slug = "old-country"

        country_service.get_by_public_id.return_value = existing_country
        country_service.get_by_name.return_value = None
        country_service.get_by_code.return_value = None
        country_service.update_country.side_effect = lambda c, **kwargs: c

        current_user = MagicMock(id=10)
        use_case = UpdateCountryUseCase(country_service=country_service, current_user=current_user)

        # 1. Update name generates new slug
        country_service.get_by_slug.return_value = None
        dto = CountryDTO(name="New Country", code="NC")
        updated = await use_case.execute("pub-1", dto)
        assert updated.slug == "new-country"

        # 2. Update with conflicting explicit slug raises 409
        conflict_country = MagicMock(spec=Country)
        conflict_country.id = 2
        country_service.get_by_slug.return_value = conflict_country
        dto_conflict = CountryDTO(name="New Country", code="NC", slug="taken-slug")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute("pub-1", dto_conflict)
        assert exc_info.value.detail.get("error_code") == "COUNTRY_SLUG_EXIST"

    asyncio.run(run_test())


def test_city_slug_creation_and_uniqueness():
    async def run_test():
        city_service = AsyncMock()
        city_service.get_by_name.return_value = None
        city_service.get_all.return_value = []

        async def mock_get_by_slug(slug, **kwargs):
            if slug in ("gangtok", "gangtok-2"):
                m = MagicMock(spec=City)
                m.id = 1
                m.slug = slug
                return m
            return None

        city_service.get_by_slug.side_effect = mock_get_by_slug
        city_service.create.side_effect = lambda c, **kwargs: c

        storage_service = MagicMock()
        country_service = AsyncMock()
        country_service.get_by_public_id.return_value = MagicMock(id=5)

        current_user = MagicMock(id=10)
        use_case = CreateCityUseCase(
            service=city_service,
            storage_service=storage_service,
            country_service=country_service,
            current_user=current_user,
        )

        dto = CityDTO(name="Gangtok", country_id="country-pub-id")
        created = await use_case.execute(dto)
        assert created.slug == "gangtok-3"
        assert created.name == "Gangtok"

    asyncio.run(run_test())


def test_city_slug_update():
    async def run_test():
        city_service = AsyncMock()
        existing_city = MagicMock(spec=City)
        existing_city.id = 1
        existing_city.name = "Old City"
        existing_city.slug = "old-city"
        existing_city.image_url = None

        city_service.get_by_public_id.return_value = existing_city
        city_service.get_by_name.return_value = None
        city_service.get_all.return_value = [existing_city]
        city_service.update.side_effect = lambda c, **kwargs: c

        country_service = AsyncMock()
        country_service.get_by_public_id.return_value = MagicMock(id=5)

        storage_service = MagicMock()
        current_user = MagicMock(id=10)
        use_case = UpdateCityUseCase(
            service=city_service,
            country_service=country_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        # 1. Update name auto-updates slug
        city_service.get_by_slug.return_value = None
        dto = CityDTO(name="Darjeeling", country_id="country-pub-id")
        updated = await use_case.execute("city-pub-id", dto)
        assert updated.slug == "darjeeling"

        # 2. Conflicting custom slug raises 409
        other_city = MagicMock(spec=City)
        other_city.id = 2
        city_service.get_by_slug.return_value = other_city
        dto_conflict = CityDTO(name="Darjeeling", country_id="country-pub-id", slug="taken-slug")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute("city-pub-id", dto_conflict)
        assert exc_info.value.detail.get("error_code") == "CITY_SLUG_EXIST"

    asyncio.run(run_test())


def test_location_slug_creation_and_uniqueness():
    async def run_test():
        location_service = AsyncMock()
        location_service.location_repository = AsyncMock()
        location_service.location_repository.get_by_name_and_city_id.return_value = None
        location_service.location_repository.get_by_id_with_city_country.return_value = None

        async def mock_get_by_slug_and_city_id(slug, city_id, **kwargs):
            if slug in ("mg-marg", "mg-marg-2") and city_id == 5:
                m = MagicMock(spec=Location)
                m.id = 1
                m.slug = slug
                m.city_id = 5
                return m
            return None

        location_service.get_by_slug_and_city_id.side_effect = mock_get_by_slug_and_city_id
        location_service.create.side_effect = lambda l, **kwargs: l

        city_service = AsyncMock()
        city_mock = MagicMock(spec=City)
        city_mock.id = 5
        city_service.get_by_public_id.return_value = city_mock

        current_user = MagicMock(id=10)
        use_case = CreateLocationUseCase(
            service=location_service,
            city_service=city_service,
            current_user=current_user,
        )

        dto = LocationDTO(name="MG Marg", city_id="city-pub-id")
        created = await use_case.execute(dto)
        assert created.slug == "mg-marg-3"
        assert created.name == "MG Marg"
        assert created.city_id == 5

    asyncio.run(run_test())


def test_location_slug_update():
    async def run_test():
        location_service = AsyncMock()
        existing_location = MagicMock(spec=Location)
        existing_location.id = 1
        existing_location.name = "Old Location"
        existing_location.slug = "old-location"
        existing_location.city_id = 5

        location_service.get_by_public_id.return_value = existing_location
        location_service.get_by_name_and_city_id.return_value = None
        location_service.update.side_effect = lambda l, **kwargs: l

        city_service = AsyncMock()
        city_mock = MagicMock(spec=City)
        city_mock.id = 5
        city_service.get_by_public_id.return_value = city_mock

        current_user = MagicMock(id=10)
        use_case = UpdateLocationUseCase(
            service=location_service,
            city_service=city_service,
            current_user=current_user,
        )

        # 1. Update location name updates slug
        location_service.get_by_slug_and_city_id.return_value = None
        dto = UpdateLocationDTO(name="Mall Road", city_id="city-pub-id")
        updated = await use_case.execute("loc-pub-id", dto)
        assert updated.slug == "mall-road"

        # 2. Conflicting custom slug raises 409
        other_loc = MagicMock(spec=Location)
        other_loc.id = 2
        location_service.get_by_slug_and_city_id.return_value = other_loc
        dto_conflict = UpdateLocationDTO(name="Mall Road", city_id="city-pub-id", slug="taken-slug")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute("loc-pub-id", dto_conflict)
        assert exc_info.value.detail.get("error_code") == "LOCATION_SLUG_EXIST"

    asyncio.run(run_test())


def test_model_and_schema_slug_fields():
    # Schema test
    country_data = {"name": "Bhutan", "code": "BT", "slug": "bhutan", "status": "active"}
    country_schema = CountrySchema(**country_data)
    assert country_schema.slug == "bhutan"

    city_data = {"name": "Thimphu", "slug": "thimphu", "status": "active"}
    city_schema = CitySchema(**city_data)
    assert city_schema.slug == "thimphu"

    loc_data = {"name": "Clock Tower", "slug": "clock-tower", "status": "active"}
    loc_schema = LocationSchema(**loc_data)
    assert loc_schema.slug == "clock-tower"

    # Model columns check
    assert hasattr(Country, "slug")
    assert hasattr(City, "slug")
    assert hasattr(Location, "slug")


def test_populate_existing_slugs():
    async def run_test():
        from app.utils.slug_backfill import populate_existing_slugs

        # Mock session
        session = AsyncMock()

        c1 = Country(id=1, name="India", code="IN", slug=None)
        c2 = Country(id=2, name="Nepal", code="NP", slug="")
        city1 = City(id=1, name="Kathmandu", country_id=2, slug=None)
        loc1 = Location(id=1, name="Thamel", city_id=1, slug=None)

        # First query returns countries, second cities, third locations
        # Subsequent queries are uniqueness checks (which return None/empty)
        country_result = MagicMock()
        country_result.scalars.return_value.all.return_value = [c1, c2]

        city_result = MagicMock()
        city_result.scalars.return_value.all.return_value = [city1]

        loc_result = MagicMock()
        loc_result.scalars.return_value.all.return_value = [loc1]

        empty_check = MagicMock()
        empty_check.first.return_value = None

        query_count = 0
        async def mock_execute(stmt):
            nonlocal query_count
            query_count += 1
            if query_count == 1:
                return country_result
            elif query_count == 2:
                return empty_check # uniqueness check for c1
            elif query_count == 3:
                return empty_check # uniqueness check for c2
            elif query_count == 4:
                return city_result
            elif query_count == 5:
                return empty_check # uniqueness check for city1
            elif query_count == 6:
                return loc_result
            else:
                return empty_check

        session.execute.side_effect = mock_execute

        stats = await populate_existing_slugs(session)

        assert stats["countries"] == 2
        assert stats["cities"] == 1
        assert stats["locations"] == 1

        assert c1.slug == "india"
        assert c2.slug == "nepal"
        assert city1.slug == "kathmandu"
        assert loc1.slug == "thamel"
        assert session.commit.called

    asyncio.run(run_test())


