import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.core.exceptions import AppException
from app.application.dto.locations.city import CityDTO
from app.application.use_case.admin.locations.city.create_city_use_case import CreateCityUseCase
from app.application.use_case.admin.locations.city.update_city_use_case import UpdateCityUseCase
from app.models.city_model import City

def test_city_dto_validation_repeating_chars():
    # Valid city name (allows double letters)
    dto = CityDTO(name="Seattle", country_id="country-id")
    assert dto.name == "Seattle"

    # Invalid city name with repeating characters (3 or more)
    with pytest.raises(AppException) as exc_info:
        CityDTO(name="amittttttttttttt", country_id="country-id")
    assert exc_info.value.detail.get("error_code") == "CITY_NAME_REPETITIVE"
    assert "repeating characters" in exc_info.value.detail.get("message")

    with pytest.raises(AppException) as exc_info:
        CityDTO(name="Pariiiis", country_id="country-id")
    assert exc_info.value.detail.get("error_code") == "CITY_NAME_REPETITIVE"


def test_city_dto_short_description_and_tag_line():
    # Valid short description and tag line
    dto = CityDTO(
        name="Kabul",
        country_id="country-id",
        short_description="dad adad dad",
        tag_line="da ad add",
    )
    assert dto.short_description == "dad adad dad"
    assert dto.tag_line == "da ad add"

    # None or whitespace values
    dto_empty = CityDTO(
        name="Kabul",
        country_id="country-id",
        short_description="   ",
        tag_line=None,
    )
    assert dto_empty.short_description is None
    assert dto_empty.tag_line is None

    # Invalid characters / script tags
    with pytest.raises(AppException) as exc_info:
        CityDTO(
            name="Kabul",
            country_id="country-id",
            short_description="<script>alert(1)</script>",
        )
    assert exc_info.value.detail.get("error_code") == "SHORT_DESCRIPTION_INVALID"

    # Repetitive characters
    with pytest.raises(AppException) as exc_info:
        CityDTO(
            name="Kabul",
            country_id="country-id",
            short_description="Great ciiityyyyy",
        )
    assert exc_info.value.detail.get("error_code") == "SHORT_DESCRIPTION_REPETITIVE"

    # Too long
    with pytest.raises(AppException) as exc_info:
        CityDTO(
            name="Kabul",
            country_id="country-id",
            tag_line="a" * 80,
        )
    assert exc_info.value.detail.get("error_code") == "TAG_LINE_TOO_LONG"


def test_city_dto_is_featured():
    # String 'true' converts to bool True
    dto1 = CityDTO(name="Kabul", country_id="cid", is_featured="true")
    assert dto1.is_featured is True

    # String 'false' converts to bool False
    dto2 = CityDTO(name="Kabul", country_id="cid", is_featured="false")
    assert dto2.is_featured is False

    # Boolean True
    dto3 = CityDTO(name="Kabul", country_id="cid", is_featured=True)
    assert dto3.is_featured is True

    # Boolean False
    dto4 = CityDTO(name="Kabul", country_id="cid", is_featured=False)
    assert dto4.is_featured is False

    # None defaults to False
    dto5 = CityDTO(name="Kabul", country_id="cid", is_featured=None)
    assert dto5.is_featured is False

def test_create_city_use_case_similarity():
    async def run_test():
        city_service = AsyncMock()
        # Mock existing cities in the DB
        existing_city = MagicMock(spec=City)
        existing_city.name = "Paris"
        existing_city.id = 1
        city_service.get_all.return_value = [existing_city]
        city_service.get_by_name.return_value = None

        storage_service = MagicMock()
        country_service = AsyncMock()
        country_service.get_by_public_id.return_value = MagicMock(id=10)

        current_user = MagicMock()
        current_user.id = 99

        use_case = CreateCityUseCase(
            service=city_service,
            storage_service=storage_service,
            country_service=country_service,
            current_user=current_user
        )

        # Exact match check first
        city_service.get_by_name.return_value = existing_city
        dto_exact = CityDTO(name="Paris", country_id="country-public-id")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto_exact)
        assert exc_info.value.detail.get("error_code") == "CITY_ALREADY_EXISTS"

        # Similarity check: "Parris" is similar to "Paris"
        city_service.get_by_name.return_value = None
        dto_similar = CityDTO(name="Parris", country_id="country-public-id")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto_similar)
        assert exc_info.value.detail.get("error_code") == "CITY_NAME_TOO_SIMILAR"
        assert "too similar to an existing city" in exc_info.value.detail.get("message")

        # Non-similar name: "Tokyo" should pass
        tokyo_mock = MagicMock(spec=City)
        tokyo_mock.name = "Tokyo"
        city_service.create.return_value = tokyo_mock
        dto_ok = CityDTO(name="Tokyo", country_id="country-public-id")
        res = await use_case.execute(dto_ok)
        assert res.name == "Tokyo"


    asyncio.run(run_test())

def test_update_city_use_case_similarity():
    async def run_test():
        city_service = AsyncMock()
        existing_city_1 = MagicMock(spec=City)
        existing_city_1.name = "Paris"
        existing_city_1.id = 1
        existing_city_1.public_id = "paris-pub-id"

        existing_city_2 = MagicMock(spec=City)
        existing_city_2.name = "Tokyo"
        existing_city_2.id = 2
        existing_city_2.public_id = "tokyo-pub-id"

        city_service.get_by_public_id.return_value = existing_city_1
        city_service.get_all.return_value = [existing_city_1, existing_city_2]
        city_service.get_by_name.return_value = None
        city_service.update.return_value = existing_city_1

        country_service = AsyncMock()
        country_service.get_by_public_id.return_value = MagicMock(id=10)

        storage_service = MagicMock()
        current_user = MagicMock()
        current_user.id = 99

        use_case = UpdateCityUseCase(
            service=city_service,
            country_service=country_service,
            storage_service=storage_service,
            current_user=current_user
        )

        # 1. Update name to its own similar variation (should not check similarity against itself)
        dto_self = CityDTO(name="Paris", country_id="country-pub-id")
        await use_case.execute("paris-pub-id", dto_self)
        
        # 2. Update name to a name similar to ANOTHER existing city (e.g. "Tokyoo" similar to "Tokyo" ID 2)
        dto_similar = CityDTO(name="Tokyoo", country_id="country-pub-id")
        with pytest.raises(AppException) as exc_info:
            await use_case.execute("paris-pub-id", dto_similar)
        assert exc_info.value.detail.get("error_code") == "CITY_NAME_TOO_SIMILAR"

    asyncio.run(run_test())
