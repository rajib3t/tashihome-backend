from typing import Optional

from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.property_model import Property
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService


class GetPropertyUseCase(BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        storage_service : StorageService
        ):
        self.property_service = property_service
        self.storage_service = storage_service

    async def execute(self, property_id: str) -> Optional[Property]:
        property_data = await self.property_service.get_by_public_id(
            property_id,
            with_relations={
                "city": True,
                "location": True,
                "vendor": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
            },
        )
        if not property_data:
            raise AppException(
                message="Property not found",
                error_code="PROPERTY_NOT_FOUND",
                status_code=404,
            )

        

        return property_data

        
