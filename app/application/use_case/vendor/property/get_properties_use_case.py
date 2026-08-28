from app.application.dto.properties.property import PropertyQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.property_model import Property, PropertyStatus
from app.repositories.base_repository import Page
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService



class GetVendorPropertyUseCase(BaseUseCase):

    def __init__(
        self,
        property_service: PropertyService,
        storage_service: StorageService,
        verify_csrf:bool,
        current_user: CurrentUser,
    ):
        self.property_service = property_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(self, params: PropertyQueryDTO) -> Page:
        vendor_id = self.current_user.id
        filters = list(params.filters or [])
        filters.append({"name": "vendor_id", "value": vendor_id})

        if params.name:
            filters.append({"name": "name", "value": params.name})

        if params.status:
            normalized_status = params.status.strip().lower()
            if normalized_status not in ["active", "inactive", "draft", "archived"]:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active' or 'inactive' or 'draft' or 'archived'.",
                    field="status",
                    error_code="STATUS_INVALID",
                )
        else:
            normalized_status = None

        if normalized_status == "active":
            filters.append({"name": "status", "value": PropertyStatus.ACTIVE})
        elif normalized_status == "inactive":
            filters.append({"name": "status", "value": PropertyStatus.INACTIVE})
        elif normalized_status == "draft":
            filters.append({"name": "status", "value": PropertyStatus.DRAFT})
        elif normalized_status == "archived":
            filters.append({"name": "status", "value": PropertyStatus.ARCHIVED})

        properties_page = await self.property_service.list(
            page=params.page,
            page_size=params.size,
            search=params.name,
            filters=filters,
            with_relations={
                "city": True,
                "location": True,
                "vendor": False,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
                "property_assets": True,
            },
            flush=True,
        )

        # Serialize properties to avoid lazy loading issues during response validation
        serialized_items = []
        for property_data in properties_page.items:
            serialized_property = await self._serialize_property(property_data)
            serialized_items.append(serialized_property)

        properties_page.items = serialized_items
        return properties_page

    async def _serialize_property(self, property_data: Property) -> dict:
            return {
                "internal_id": property_data.id,
                "id": str(property_data.public_id),
                "name": property_data.name,
                "slug": property_data.slug,
                
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
                "is_featured": property_data.is_featured ,
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

