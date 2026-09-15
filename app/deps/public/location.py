from fastapi import Depends

from app.application.use_case.public.location.get_locations_use_case import (
    PublicGetLocationsUseCase,
    PublicGetLocationUseCase,
)
from app.deps.service import (
    get_city_service,
    get_location_service,
    get_storage_service,
)
from app.services.city_service import CityService
from app.services.location_service import LocationService
from app.services.storage_service import StorageService


async def get_public_get_locations_use_case(
    location_service: LocationService = Depends(get_location_service),
    city_service: CityService = Depends(get_city_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> PublicGetLocationsUseCase:
    return PublicGetLocationsUseCase(
        location_service=location_service,
        city_service=city_service,
        storage_service=storage_service,
    )


async def get_public_get_location_use_case(
    location_service: LocationService = Depends(get_location_service),
) -> PublicGetLocationUseCase:
    return PublicGetLocationUseCase(
        location_service=location_service,
    )

