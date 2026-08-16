from app.application.dto.properties.property import AssetsDTO, PropertyAssetsDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.property_asset_model import PropertyAsset, PropertyAssetType, PropertyAssetUseFor
from app.models.property_model import Property
from app.services.property_asset_service import PropertyAssetService
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService


class UploadPropertyAssetsUseCase(PropertySerializerMixin, BaseUseCase):
    FILE_UPLOAD_RULES = {
        "files": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg"),
            "max_size_bytes": 5 * 1024 * 1024,
        },
    }

    def __init__(
        self,
        property_service: PropertyService,
        property_asset_service: PropertyAssetService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.property_service = property_service
        self.property_asset_service = property_asset_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(
        self,
        property_id: str,
        data: PropertyAssetsDTO,
    ) -> Property:
        property_ = await self.property_service.get_by_public_id(property_id, flush=True)
        if not property_:
            raise AppException(
                status_code=404,
                message="Property not found.",
                field="property_id",
                error_code="PROPERTY_NOT_FOUND",
            )

        gallery_images = data.gallery_images or []
        asset_entries: list[tuple[AssetsDTO, PropertyAssetUseFor]] = [
            (image, PropertyAssetUseFor.GALLERY) for image in gallery_images if image.file is not None
        ]
        if data.feature_image and data.feature_image.file is not None:
            asset_entries.append((data.feature_image, PropertyAssetUseFor.FEATURE))
        if data.cover_image and data.cover_image.file is not None:
            asset_entries.append((data.cover_image, PropertyAssetUseFor.COVER))

        # Handle FEATURE and COVER replacement logic
        use_for_types_to_replace = {PropertyAssetUseFor.FEATURE, PropertyAssetUseFor.COVER}
        for use_for in use_for_types_to_replace:
            has_new_upload = any(asset_use_for == use_for for _, asset_use_for in asset_entries)
            if has_new_upload:
                existing_assets = await self.property_asset_service.get_by_property_id_and_use_for(
                    property_.id, use_for, flush=True
                )
                for existing_asset in existing_assets:
                    try:
                        await self.storage_service.delete_object(existing_asset.file_url)
                    except Exception:
                        pass
                    await self.property_asset_service.delete(existing_asset, commit=True)

        if not asset_entries:
            raise AppException(
                status_code=400,
                message="At least one file is required.",
                field="gallery_images",
                error_code="INVALID_FILE",
            )

        for index, (asset_input, use_for) in enumerate(asset_entries):
            upload = asset_input.file
            if upload is None:
                continue
            file_key = await self._upload_file(
                upload,
                folder=f"properties/{property_.public_id}",
                field_name="files",
                webp=True,
            )
            asset = PropertyAsset(
                property_id=property_.id,
                asset_type=PropertyAssetType.IMAGE,
                use_for=use_for,
                file_url=file_key,
                title=asset_input.name or upload.filename,
                is_primary=use_for == PropertyAssetUseFor.FEATURE or (use_for == PropertyAssetUseFor.GALLERY and index == 0),
                sort_order=index,
                created_by=self.current_user.id,
                updated_by=self.current_user.id,
            )
            await self.property_asset_service.create(asset, commit=True)

        # Re-fetch the full property with all relations, matching the standard property response
        full_property = await self.property_service.get_by_public_id(
            property_id,
            with_relations={
                "vendor": True,
                "city": True,
                "location": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
                "property_assets": True,
            },
            flush=True,
        ) or property_
        return await self.serialize_property(full_property)


class DeletePropertyAssetUseCase(PropertySerializerMixin, BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        property_asset_service: PropertyAssetService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.property_service = property_service
        self.property_asset_service = property_asset_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, property_id: str, asset_id: str) -> Property:
        property_ = await self.property_service.get_by_public_id(property_id, flush=True)
        if not property_:
            raise AppException(
                status_code=404,
                message="Property not found.",
                field="property_id",
                error_code="PROPERTY_NOT_FOUND",
            )

        asset = await self.property_asset_service.get_by_public_id(asset_id, flush=True)
        if not asset:
            raise AppException(
                status_code=404,
                message="Property asset not found.",
                field="asset_id",
                error_code="PROPERTY_ASSET_NOT_FOUND",
            )
        if asset.property_id != property_.id:
            raise AppException(
                status_code=403,
                message="You are not authorized to delete this property asset.",
                field="asset_id",
                error_code="PROPERTY_ASSET_NOT_FOUND",
            )
        try:
            await self.storage_service.delete_object(asset.file_url)
        except Exception:
            pass
        await self.property_asset_service.delete(asset, commit=True)

        # Re-fetch the full property with all relations, matching the standard property response
        full_property = await self.property_service.get_by_public_id(
            property_id,
            with_relations={
                "vendor": True,
                "city": True,
                "location": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
                "property_assets": True,
            },
            flush=True,
        )
        return await self.serialize_property(full_property)