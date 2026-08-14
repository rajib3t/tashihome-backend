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

    async def execute(self, property_id: str) -> Optional[dict]:
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
                "property_assets": True,
            },
        )
        
        print(
            "facilities:", len(property_data.property_facilities or []),
            "amenities:", len(property_data.property_amenities or []),
            "room_types:", len(property_data.property_room_types or []),
            "assets:", len(property_data.property_assets or []),
        )
        if not property_data:
            raise AppException(
                message="Property not found",
                error_code="PROPERTY_NOT_FOUND",
                status_code=404,
            )

        return await self._serialize_property(property_data)

    async def _serialize_property(self, property_data: Property) -> dict:
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
            "property_assets": await self._serialize_property_assets(property_data.property_assets or []),
            "gallery_images": await self._serialize_assets_by_use_for(property_data.property_assets or [], "gallery"),
            "feature_image": await self._serialize_single_asset_by_use_for(property_data.property_assets or [], "feature"),
            "cover_image": await self._serialize_single_asset_by_use_for(property_data.property_assets or [], "cover"),
            "status": property_data.status.value if hasattr(property_data.status, "value") else property_data.status,
        }

    async def _serialize_property_assets(self, property_assets) -> list[dict]:
        assets = []
        for asset in property_assets:
            asset_dict = {
                "id": str(asset.public_id) if getattr(asset, "public_id", None) is not None else None,
                "asset_type": asset.asset_type.value if hasattr(asset.asset_type, "value") else asset.asset_type,
                "use_for": asset.use_for.value if hasattr(asset.use_for, "value") else asset.use_for,
                "file_url": asset.file_url,
                "title": asset.title,
                "is_primary": asset.is_primary,
                "sort_order": asset.sort_order,
                "status": asset.status.value if hasattr(asset.status, "value") else asset.status,
            }
            # Generate presigned URL for the file
            if asset.file_url:
                try:
                    asset_dict["file_url"] = await self.storage_service.generate_presigned_url(asset.file_url)
                except Exception:
                    # If presigned URL generation fails, keep the original file_url
                    pass
            assets.append(asset_dict)
        return assets

    async def _serialize_assets_by_use_for(self, property_assets, use_for: str) -> list[dict]:
        """Serialize assets filtered by use_for type (e.g., gallery images)"""
        filtered_assets = [
            asset for asset in property_assets
            if hasattr(asset, 'use_for') and asset.use_for.value == use_for
        ]
        return await self._serialize_property_assets(filtered_assets)

    async def _serialize_single_asset_by_use_for(self, property_assets, use_for: str) -> dict | None:
        """Serialize a single asset by use_for type (e.g., feature or cover image)"""
        filtered_assets = [
            asset for asset in property_assets
            if hasattr(asset, 'use_for') and asset.use_for.value == use_for
        ]
        if filtered_assets:
            serialized = await self._serialize_property_assets(filtered_assets)
            return serialized[0] if serialized else None
        return None

        
