from typing import Optional

from app.core.exceptions import AppException
from app.models.property_model import PropertyStatus
from app.services.location_service import LocationService
from app.services.city_service import CityService
from app.repositories.base_repository import Page
from app.application.dto.properties.public.property import PublicPropertyQueryDTO
from app.services.storage_service import StorageService
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService
from app.application.use_case.base_use_case import BaseUseCase
from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin

class PublicPropertiesUseCase(BaseUseCase, PropertySerializerMixin):
    def __init__(
        self,
        property_service: PropertyService,
        storage_service: StorageService,
        city_service: CityService,
        location_service: LocationService,
        review_service: Optional[ReviewService] = None,
    ):
        self.property_service = property_service
        self.storage_service = storage_service
        self.city_service = city_service
        self.location_service = location_service
        self.review_service = review_service


    async def execute(self, params: PublicPropertyQueryDTO) -> Page:
        # Validate UUIDs if provided and ensure entities exist when querying by ID
        if params.city_id:
            city = await self.city_service.get_by_public_id(params.city_id, flush=True)
            if not city:
                raise AppException(
                    status_code=404,
                    message="City not found.",
                    field="city_id",
                    error_code="CITY_NOT_FOUND",
                )

        if params.location_id:
            location = await self.location_service.get_by_public_id(params.location_id, flush=True)
            if not location:
                raise AppException(
                    status_code=404,
                    message="Location not found.",
                    field="location_id",
                    error_code="LOCATION_NOT_FOUND",
                )

        if params.city_slug:
            city = await self.city_service.get_by_slug(params.city_slug, flush=True)
            if not city:
                raise AppException(
                    status_code=404,
                    message="City with given slug not found.",
                    field="city_slug",
                    error_code="CITY_NOT_FOUND",
                )

        if params.location_slug:
            location = await self.location_service.get_by_slug(params.location_slug, flush=True)
            if not location:
                raise AppException(
                    status_code=404,
                    message="Location with given slug not found.",
                    field="location_slug",
                    error_code="LOCATION_NOT_FOUND",
                )

        properties_page = await self.property_service.search_stays(
            city_slug=params.city_slug,
            location_slug=params.location_slug,
            country_slug=params.country_slug,
            city_id=params.city_id,
            location_id=params.location_id,
            country_id=params.country_id,
            min_price=params.min_price,
            max_price=params.max_price,
            is_featured=params.is_featured,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            page=params.page,
            page_size=params.size,
            with_relations={
                "city": True,
                "location": True,
                "property_assets": True,
            },
            flush=True,
        )

        # Fetch rating summaries for properties if review_service is available
        rating_summaries = {}
        if self.review_service and properties_page.items:
            property_ids = [p.id for p in properties_page.items if p.id]
            rating_summaries = await self.review_service.get_properties_rating_summary(property_ids)

        # Serialize properties to avoid lazy loading issues during response validation
        items = []
        for property_data in properties_page.items:
            rating_summary = rating_summaries.get(property_data.id)
            serialized = await self.serialize_property_list_item(property_data, rating_summary=rating_summary)
            items.append(serialized)

        properties_page.items = items
        return properties_page



        