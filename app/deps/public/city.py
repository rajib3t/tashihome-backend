from app.deps.service import get_city_service
from app.deps.service import get_storage_service
from app.deps.service import get_country_service
from app.application.use_case.public.city.get_cities_use_case import PublicGetCitiesUseCase
from app.application.dto.locations.public.city import PublicCityQueryDTO
from app.services.country_service import CountryService
from app.services.storage_service import StorageService
from app.services.city_service import CityService
from app.deps.auth import get_current_user

from fastapi import Depends


async def get_public_get_cities_use_case(
    city_service: CityService = Depends(get_city_service),
    country_service: CountryService = Depends(get_country_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> PublicGetCitiesUseCase:
    return PublicGetCitiesUseCase(
        city_service=city_service,
        country_service=country_service,
        storage_service=storage_service,
    )