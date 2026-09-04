from fastapi import Depends
from app.application.use_case.public.stay.search_stays_use_case import PublicSearchStaysUseCase
from app.application.use_case.public.property.get_property_use_case import PublicGetPropertyUseCase
from app.deps.service import (
    get_booking_service,
    get_city_service,
    get_location_service,
    get_property_service,
    get_review_service,
    get_storage_service,
)
from app.services.booking_service import BookingService
from app.services.city_service import CityService
from app.services.location_service import LocationService
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService
from app.services.storage_service import StorageService


async def public_search_stays_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
    city_service: CityService = Depends(get_city_service),
    location_service: LocationService = Depends(get_location_service),
    review_service: ReviewService = Depends(get_review_service),
) -> PublicSearchStaysUseCase:
    return PublicSearchStaysUseCase(
        property_service=property_service,
        storage_service=storage_service,
        city_service=city_service,
        location_service=location_service,
        review_service=review_service,
    )


async def public_get_stay_use_case(
    property_service: PropertyService = Depends(get_property_service),
    storage_service: StorageService = Depends(get_storage_service),
    booking_service: BookingService = Depends(get_booking_service),
    review_service: ReviewService = Depends(get_review_service),
) -> PublicGetPropertyUseCase:
    return PublicGetPropertyUseCase(
        property_service=property_service,
        storage_service=storage_service,
        booking_service=booking_service,
        review_service=review_service,
    )

