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
        
        print(
            "facilities:", len(property_data.property_facilities or []),
            "amenities:", len(property_data.property_amenities or []),
            "room_types:", len(property_data.property_room_types or []),
        )
        if not property_data:
            raise AppException(
                message="Property not found",
                error_code="PROPERTY_NOT_FOUND",
                status_code=404,
            )

        return self._serialize_property(property_data)

    @staticmethod
    def _serialize_property(property_data: Property) -> dict:
        return {
            "internal_id": property_data.id,
            "id": str(property_data.public_id),
            "name": property_data.name,
            "slug": property_data.slug,
            "vendor": (
                {
                    "id": str(property_data.vendor.public_id),
                    "full_name": property_data.vendor.full_name,
                    "email": property_data.vendor.email,
                }
                if property_data.vendor
                else None
            ),
            "location": (
                {
                    "id": str(property_data.location.public_id),
                    "name": property_data.location.name,
                }
                if property_data.location
                else None
            ),
            "city": (
                {
                    "id": str(property_data.city.public_id),
                    "name": property_data.city.name,
                }
                if property_data.city
                else None
            ),
            "room_type": None,
            "currency": property_data.currency,
            "type": property_data.type.value if hasattr(property_data.type, "value") else property_data.type,
            "price_per_night": float(property_data.price_per_night) if property_data.price_per_night is not None else None,
            "sale_per_night": float(property_data.sale_per_night) if property_data.sale_per_night is not None else None,
            "address": property_data.address,
            "latitude": float(property_data.latitude) if property_data.latitude is not None else None,
            "longitude": float(property_data.longitude) if property_data.longitude is not None else None,
            "description": property_data.description,
            "property_room_types": [
                {
                    "id": str(item.public_id) if getattr(item, "public_id", None) is not None else None,
                    "room_type": (
                        {
                            "id": str(item.room_type.public_id),
                            "name": item.room_type.name,
                            "capacity": item.room_type.capacity,
                        }
                        if getattr(item, "room_type", None)
                        else None
                    ),
                }
                for item in (property_data.property_room_types or [])
            ],
            "property_amenities": [
                {
                    "id": str(item.public_id) if getattr(item, "public_id", None) is not None else None,
                    "amenity": (
                        {
                            "id": str(item.amenity.public_id),
                            "name": item.amenity.name,
                            "icon_url": item.amenity.icon_url,
                        }
                        if getattr(item, "amenity", None)
                        else None
                    ),
                }
                for item in (property_data.property_amenities or [])
            ],
            "property_facilities": [
                {
                    "id": str(item.public_id) if getattr(item, "public_id", None) is not None else None,
                    "facility": (
                        {
                            "id": str(item.facility.public_id),
                            "name": item.facility.name,
                            "icon_url": item.facility.icon_url,
                        }
                        if getattr(item, "facility", None)
                        else None
                    ),
                }
                for item in (property_data.property_facilities or [])
            ],
            "property_food_options": [
                {
                    "id": str(item.public_id) if getattr(item, "public_id", None) is not None else None,
                    "name": item.name,
                    "is_included": item.is_included,
                }
                for item in (property_data.property_food_options or [])
            ],
            "debug_counts": {
                "property_room_types": len(property_data.property_room_types or []),
                "property_amenities": len(property_data.property_amenities or []),
                "property_facilities": len(property_data.property_facilities or []),
                "property_food_options": len(property_data.property_food_options or []),
            },
            "status": property_data.status.value if hasattr(property_data.status, "value") else property_data.status,
        }

        
