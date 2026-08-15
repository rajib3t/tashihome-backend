from typing import Optional

from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService


class PublicGetPropertyUseCase(BaseUseCase, PropertySerializerMixin):
    def __init__(
            self,
            property_service: PropertyService,
            storage_service: StorageService,
        ):
            self.property_service = property_service
            self.storage_service = storage_service
    
    async def execute(self, slug: str) -> Optional[dict]:
        property_data = await self.property_service.get_by_slug(
            slug,
            with_relations={
                "city": True,
                "location": True,
                "vendor": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
                "property_assets": True,
            },
        )

        if not property_data:
            raise AppException(
                message="Property not found",
                error_code="PROPERTY_NOT_FOUND",
                status_code=404,
            )

        return await self.serialize_property(property_data)