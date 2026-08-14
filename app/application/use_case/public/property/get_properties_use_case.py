from app.core.exceptions import AppException
from app.models.property_model import PropertyStatus
from app.services.location_service import LocationService
from app.services.city_service import CityService
from app.repositories.base_repository import Page
from app.application.dto.properties.public.property import PublicPropertyQueryDTO
from app.services.storage_service import StorageService
from app.services.property_service import PropertyService
from app.application.use_case.base_use_case import BaseUseCase
from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin

class PublicPropertiesUseCase(BaseUseCase, PropertySerializerMixin):
    def __init__(
        self,
        property_service : PropertyService,
        storage_service : StorageService,
        city_service : CityService,
        location_service : LocationService,
    ):
        self.property_service = property_service
        self.storage_service = storage_service
        self.city_service = city_service
        self.location_service = location_service

    async def execute(self, params : PublicPropertyQueryDTO) -> Page:
        filters = list(params.filters or [])
        filters.append({"name": "status", "value": PropertyStatus.ACTIVE})  # Only fetch active properties
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
        if params.location_id:
            location = await self.location_service.get_by_public_id(params.location_id)
            if not location:
                raise AppException(
                    status_code=404,
                    message="Location not found.",
                    field="location_id",
                    error_code="LOCATION_NOT_FOUND",
                )
            filters.append({"name": "location_id", "value": location.id})
        if params.is_featured:
            if params.is_featured not in [True, False]:
                raise AppException(
                    status_code=422,
                    message="Invalid is_featured filter. Must be 'true' or 'false'.",
                    field="is_featured",
                    error_code="IS_FEATURED_INVALID",
                )
            if params.is_featured:
                filters.append({"name": "is_featured", "value": True})
            else:
                filters.append({"name": "is_featured", "value": False})
        
        print(f"Filters applied: {filters}")  # Debugging line to check filters
        properties_page = await self.property_service.list(
                page=params.page,
                page_size=params.size,
                filters=filters,
                with_relations={
                    "city": True,
                    "location": True,
        
                    "property_assets": True,
                },
                flush=True,
            )

        
        # Serialize properties to avoid lazy loading issues during response validation
        items = []
        for property_data in properties_page.items:
            serialized = await self.serialize_property_list_item(property_data)
            items.append(serialized)

        properties_page.items = items
        return properties_page


        