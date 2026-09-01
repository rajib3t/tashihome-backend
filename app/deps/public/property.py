from fastapi import Depends
from app.application.use_case.public.property.get_properties_use_case import PublicPropertiesUseCase
from app.application.use_case.public.property.get_property_use_case import PublicGetPropertyUseCase
from app.deps.service import (
    get_booking_service,
    get_city_service,
    get_location_service,
    get_property_service,
    get_storage_service,
)
from app.services.booking_service import BookingService
from app.services.city_service import CityService
from app.services.location_service import LocationService
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService


async def public_properties_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
    city_service: CityService = Depends(get_city_service),
    location_service: LocationService = Depends(get_location_service),
) -> PublicPropertiesUseCase:
    return PublicPropertiesUseCase(
        property_service=property_service,
        storage_service=storage_service,
        city_service=city_service,
        location_service=location_service,
    )


async def public_get_property_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
    booking_service: BookingService = Depends(get_booking_service),
) -> PublicGetPropertyUseCase:
    return PublicGetPropertyUseCase(
        property_service=property_service,
        storage_service=storage_service,
        booking_service=booking_service,
    )