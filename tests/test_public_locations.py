import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.application.dto.locations.public.location import PublicLocationQueryDTO
from app.application.use_case.public.location.get_locations_use_case import (
    PublicGetLocationsUseCase,
    PublicGetLocationUseCase,
)
from app.core.exceptions import AppException
from app.models.city_model import City
from app.models.location_model import Location, LocationStatus
from app.repositories.base_repository import Page
from app.api.public.location.location_route import router, controller


def test_public_location_query_dto_validation():
    # Valid default query
    dto = PublicLocationQueryDTO()
    assert dto.page == 1
    assert dto.size == 10
    assert dto.sort_by == "created_at"
    assert dto.sort_order == "desc"

    # Invalid page
    with pytest.raises(AppException) as exc:
        PublicLocationQueryDTO(page=0)
    assert exc.value.error_code == "PAGINATION_INVALID"

    # Invalid size > 100
    with pytest.raises(AppException) as exc:
        PublicLocationQueryDTO(size=101)
    assert exc.value.error_code == "PAGINATION_INVALID"

    # Invalid sort_by
    with pytest.raises(AppException) as exc:
        PublicLocationQueryDTO(sort_by="invalid_field")
    assert exc.value.error_code == "SORT_INVALID"

    # Invalid sort_order
    with pytest.raises(AppException) as exc:
        PublicLocationQueryDTO(sort_order="sideways")
    assert exc.value.error_code == "SORT_INVALID"


def test_public_get_locations_use_case_success():
    async def run():
        location_service = AsyncMock()
        city_service = AsyncMock()
        storage_service = MagicMock()

        mock_loc = MagicMock(spec=Location)
        mock_loc.id = 1
        mock_loc.name = "Downtown"
        mock_loc.slug = "downtown"
        mock_loc.image_url = "https://example.com/loc.jpg"
        mock_loc.status = LocationStatus.ACTIVE

        location_service.list.return_value = Page(
            items=[mock_loc],
            total=1,
            page=1,
            page_size=10,
        )

        use_case = PublicGetLocationsUseCase(
            location_service=location_service,
            city_service=city_service,
            storage_service=storage_service,
        )

        params = PublicLocationQueryDTO(search="down")
        result = await use_case.execute(params)

        assert len(result.items) == 1
        assert result.items[0].name == "Downtown"
        assert result.items[0].image_url == "https://example.com/loc.jpg"

        location_service.list.assert_awaited_once()
        call_kwargs = location_service.list.call_args.kwargs
        assert call_kwargs["page"] == 1
        assert call_kwargs["page_size"] == 10
        assert call_kwargs["search"] == "down"
        assert {"name": "status", "value": LocationStatus.ACTIVE} in call_kwargs["filters"]
        assert call_kwargs["with_relations"] == {"city": True}

    asyncio.run(run())


def test_public_get_locations_use_case_with_city_filter():
    async def run():
        location_service = AsyncMock()
        city_service = AsyncMock()
        storage_service = MagicMock()

        mock_city = MagicMock(spec=City)
        mock_city.id = 42
        city_service.get_by_public_id.return_value = mock_city

        location_service.list.return_value = Page(
            items=[],
            total=0,
            page=1,
            page_size=10,
        )

        use_case = PublicGetLocationsUseCase(
            location_service=location_service,
            city_service=city_service,
            storage_service=storage_service,
        )

        params = PublicLocationQueryDTO(city_id="city-uuid-123")
        result = await use_case.execute(params)

        city_service.get_by_public_id.assert_awaited_once_with("city-uuid-123")
        call_filters = location_service.list.call_args.kwargs["filters"]
        assert {"name": "city_id", "value": 42} in call_filters
        assert {"name": "status", "value": LocationStatus.ACTIVE} in call_filters

    asyncio.run(run())


def test_public_get_locations_use_case_city_not_found():
    async def run():
        location_service = AsyncMock()
        city_service = AsyncMock()
        storage_service = MagicMock()

        city_service.get_by_public_id.return_value = None

        use_case = PublicGetLocationsUseCase(
            location_service=location_service,
            city_service=city_service,
            storage_service=storage_service,
        )

        params = PublicLocationQueryDTO(city_id="nonexistent-city")
        with pytest.raises(AppException) as exc:
            await use_case.execute(params)

        assert exc.value.status_code == 404
        assert exc.value.error_code == "CITY_NOT_FOUND"

    asyncio.run(run())


def test_public_get_location_by_slug_success():
    async def run():
        location_service = AsyncMock()
        mock_loc = MagicMock(spec=Location)
        mock_loc.slug = "gangtok-central"
        mock_loc.status = LocationStatus.ACTIVE
        location_service.get_by_slug.return_value = mock_loc

        use_case = PublicGetLocationUseCase(location_service=location_service)
        result = await use_case.execute("gangtok-central")

        assert result.slug == "gangtok-central"
        location_service.get_by_slug.assert_awaited_once_with(
            slug="gangtok-central",
            with_relations={"city": True},
        )

    asyncio.run(run())


def test_public_get_location_by_slug_not_found_or_inactive():
    async def run():
        location_service = AsyncMock()
        location_service.get_by_slug.return_value = None

        use_case = PublicGetLocationUseCase(location_service=location_service)
        with pytest.raises(AppException) as exc:
            await use_case.execute("unknown-loc")
        assert exc.value.status_code == 404
        assert exc.value.error_code == "LOCATION_NOT_FOUND"

        # Inactive location should also 404
        inactive_loc = MagicMock(spec=Location)
        inactive_loc.status = LocationStatus.INACTIVE
        location_service.get_by_slug.return_value = inactive_loc
        with pytest.raises(AppException) as exc2:
            await use_case.execute("inactive-loc")
        assert exc2.value.status_code == 404
        assert exc2.value.error_code == "LOCATION_NOT_FOUND"

    asyncio.run(run())


def test_public_location_name_filter_and_sorting():
    async def run():
        location_service = AsyncMock()
        city_service = AsyncMock()
        storage_service = MagicMock()

        mock_loc = MagicMock(spec=Location)
        mock_loc.id = 10
        mock_loc.name = "TestTest"
        mock_loc.slug = "testtest"
        mock_loc.image_url = None
        mock_loc.status = LocationStatus.ACTIVE

        location_service.list.return_value = Page(
            items=[mock_loc],
            total=1,
            page=1,
            page_size=15,
        )

        use_case = PublicGetLocationsUseCase(
            location_service=location_service,
            city_service=city_service,
            storage_service=storage_service,
        )

        # Simulating: ?page=1&size=15&name=TestTest&sortBy=name&sort_by=name&sortOrder=asc&sort_order=asc
        params = PublicLocationQueryDTO(
            page=1,
            size=15,
            name="TestTest",
            sortBy="name",
            sort_by="name",
            sortOrder="asc",
            sort_order="asc",
        )
        result = await use_case.execute(params)

        assert len(result.items) == 1
        assert result.items[0].name == "TestTest"

        location_service.list.assert_awaited_once()
        call_kwargs = location_service.list.call_args.kwargs
        assert call_kwargs["page"] == 1
        assert call_kwargs["page_size"] == 15
        assert call_kwargs["sort_by"] == "name"
        assert call_kwargs["sort_order"] == "asc"
        assert {"name": "name", "value": "TestTest"} in call_kwargs["filters"]
        assert {"name": "status", "value": LocationStatus.ACTIVE} in call_kwargs["filters"]

    asyncio.run(run())


def test_public_location_routes_registered():
    route_paths = {route.path for route in router.routes}
    assert "/locations/" in route_paths
    assert "/locations/{slug}" in route_paths


