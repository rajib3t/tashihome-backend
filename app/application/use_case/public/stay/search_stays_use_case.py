from datetime import date
from typing import Optional

from app.application.dto.stays.public.stay import PublicSearchStaysQueryDTO
from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.repositories.base_repository import Page
from app.services.city_service import CityService
from app.services.location_service import LocationService
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService


class PublicSearchStaysUseCase(BaseUseCase, PropertySerializerMixin):
    def __init__(
        self,
        property_service: PropertyService,
        storage_service: StorageService,
        city_service: CityService,
        location_service: LocationService,
    ):
        self.property_service = property_service
        self.storage_service = storage_service
        self.city_service = city_service
        self.location_service = location_service

    async def execute(self, params: PublicSearchStaysQueryDTO) -> Page:
        # Date validations
        if params.check_in_date or params.check_out_date:
            if not params.check_in_date or not params.check_out_date:
                raise AppException(
                    status_code=422,
                    message="Both check_in_date and check_out_date must be provided for date filtering.",
                    field="check_in_date",
                    error_code="DATE_RANGE_REQUIRED",
                )
            if params.check_out_date <= params.check_in_date:
                raise AppException(
                    status_code=422,
                    message="check_out_date must be strictly after check_in_date.",
                    field="check_out_date",
                    error_code="INVALID_DATE_RANGE",
                )

        # Region / Search text resolution
        region_query = params.region or params.search or params.q
        if region_query:
            region_query = region_query.strip()

        # City name resolution (supports city_name or city)
        city_name = params.city_name or params.city
        if city_name:
            city_name = city_name.strip()

        # Location name resolution (supports location_name or location)
        location_name = params.location_name or params.location
        if location_name:
            location_name = location_name.strip()

        # Country name resolution (supports country_name or country)
        country_name = params.country_name or params.country
        if country_name:
            country_name = country_name.strip()

        # Calculate guests count
        guests_count = params.guests
        if guests_count is None and (params.adults is not None or params.children is not None):
            guests_count = (params.adults or 0) + (params.children or 0)

        # Execute search query
        properties_page = await self.property_service.search_stays(
            region=region_query,
            city_name=city_name,
            location_name=location_name,
            country_name=country_name,
            city_id=params.city_id,
            location_id=params.location_id,
            country_id=params.country_id,
            check_in_date=params.check_in_date,
            check_out_date=params.check_out_date,
            guests=guests_count,
            rooms=params.rooms or 1,
            min_price=params.min_price,
            max_price=params.max_price,
            property_type=params.type,
            is_featured=params.is_featured,
            amenity_ids=params.amenity_ids,
            facility_ids=params.facility_ids,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            page=params.page,
            page_size=params.size,
            with_relations={
                "city": True,
                "location": True,
                "property_assets": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
            },
            flush=True,
        )

        # Serialize list items
        items = []
        for property_data in properties_page.items:
            serialized = await self.serialize_property_list_item(property_data)
            items.append(serialized)

        properties_page.items = items
        return properties_page

