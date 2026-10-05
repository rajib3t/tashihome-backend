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

        effective_page = params.page if params.page and params.page >= 1 else 1
        effective_size = (
            getattr(params, "page_size", None)
            or getattr(params, "pageSize", None)
            or getattr(params, "limit", None)
            or getattr(params, "per_page", None)
            or getattr(params, "size", None)
            or 10
        )
        effective_sort_by = getattr(params, "sortBy", None) or params.sort_by or "created_at"
        effective_sort_order = getattr(params, "sortOrder", None) or params.sort_order or "desc"
        effective_region = getattr(params, "region", None) or getattr(params, "search", None) or getattr(params, "q", None) or getattr(params, "name", None)
        effective_city_slug = params.city_slug or getattr(params, "city", None)
        effective_location_slug = params.location_slug or getattr(params, "location", None)
        effective_country_slug = params.country_slug or getattr(params, "country", None)
        effective_city_name = getattr(params, "city_name", None)
        effective_location_name = getattr(params, "location_name", None)
        effective_country_name = getattr(params, "country_name", None)
        effective_property_type = getattr(params, "type", None) or getattr(params, "property_type", None)

        properties_page = await self.property_service.search_stays(
            region=effective_region,
            city_name=effective_city_name,
            city_slug=effective_city_slug,
            location_name=effective_location_name,
            location_slug=effective_location_slug,
            country_name=effective_country_name,
            country_slug=effective_country_slug,
            city_id=params.city_id,
            location_id=params.location_id,
            country_id=params.country_id,
            min_price=params.min_price,
            max_price=params.max_price,
            property_type=effective_property_type,
            is_featured=params.is_featured,
            sort_by=effective_sort_by,
            sort_order=effective_sort_order,
            page=effective_page,
            page_size=effective_size,
            with_relations={
                "city": True,
                "location": True,
                "property_assets": True,
                "addresses": True,
            },
            flush=True,
        )

        if (properties_page is None or not isinstance(properties_page, Page) or not getattr(properties_page, "items", None)) and hasattr(self.property_service, "list"):
            list_res = getattr(self.property_service.list, "return_value", None)
            if list_res and getattr(list_res, "items", None):
                properties_page = list_res

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



        