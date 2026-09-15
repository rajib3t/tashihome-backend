import copy
from typing import Optional

from app.application.dto.locations.public.location import PublicLocationQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.location_model import Location, LocationStatus
from app.repositories.base_repository import Page
from app.services.city_service import CityService
from app.services.location_service import LocationService
from app.services.storage_service import StorageService


class PublicGetLocationsUseCase(BaseUseCase):
    def __init__(
        self,
        location_service: LocationService,
        city_service: CityService,
        storage_service: StorageService,
    ):
        self.location_service = location_service
        self.city_service = city_service
        self.storage_service = storage_service

    async def execute(self, params: PublicLocationQueryDTO) -> Page[Location]:
        filters = list(params.filters or [])

        if params.city_id:
            city = await self.city_service.get_by_public_id(params.city_id)
            if not city:
                raise AppException(
                    status_code=404,
                    message="City not found.",
                    field="city_id",
                    error_code="CITY_NOT_FOUND",
                )
            filters.append({"name": "city_id", "value": city.id})

        if params.name:
            filters.append({"name": "name", "value": params.name})

        filters.append({"name": "status", "value": LocationStatus.ACTIVE})

        effective_sort_by = getattr(params, "sortBy", None) or getattr(params, "sort_by", None) or "created_at"
        effective_sort_order = getattr(params, "sortOrder", None) or getattr(params, "sort_order", None) or "desc"

        locations_page = await self.location_service.list(
            page=params.page,
            page_size=params.size,
            search=params.search,
            filters=filters,
            sort_by=effective_sort_by,
            sort_order=effective_sort_order,
            with_relations={
                "city": True,
            },
        )

        updated_items = []
        for loc in locations_page.items:
            display_loc = copy.copy(loc)
            if loc.image_url:
                display_loc.image_url = loc.image_url
            updated_items.append(display_loc)

        locations_page.items = updated_items
        return locations_page


class PublicGetLocationUseCase(BaseUseCase):
    def __init__(
        self,
        location_service: LocationService,
    ):
        self.location_service = location_service

    async def execute(self, slug: str) -> Location:
        location = await self.location_service.get_by_slug(
            slug=slug,
            with_relations={"city": True},
        )
        if not location or location.status != LocationStatus.ACTIVE:
            raise AppException(
                status_code=404,
                message="Location not found.",
                field="slug",
                error_code="LOCATION_NOT_FOUND",
            )
        return location

