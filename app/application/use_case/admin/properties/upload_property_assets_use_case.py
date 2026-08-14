from app.application.dto.properties.property import AssetsDTO, PropertyAssetsDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.property_asset_model import PropertyAsset, PropertyAssetType, PropertyAssetUseFor
from app.services.property_asset_service import PropertyAssetService
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService


class UploadPropertyAssetsUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "files": {
            "allowed_prefixes": ("image/",),
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
    ) -> dict:
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
            # Check if this use_for type is in the new uploads
            has_new_upload = any(asset_use_for == use_for for _, asset_use_for in asset_entries)
            if has_new_upload:
                # Find existing assets with the same use_for for this property
                existing_assets = await self.property_asset_service.get_by_property_id_and_use_for(
                    property_.id, use_for, flush=True
                )
                for existing_asset in existing_assets:
                    # Delete from storage
                    try:
                        await self.storage_service.delete_object(existing_asset.file_url)
                    except Exception:
                        pass
                    # Delete from database
                    await self.property_asset_service.delete(existing_asset, commit=True)

        if not asset_entries:
            raise AppException(
                status_code=400,
                message="At least one file is required.",
                field="gallery_images",
                error_code="INVALID_FILE",
            )

        created_assets: list[dict] = []
        gallery_images = []
        feature_image = None
        cover_image = None
        
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
            created_asset = await self.property_asset_service.create(asset, commit=True)
            
            # Generate presigned URL for the file
            file_url = file_key
            try:
                file_url = await self.storage_service.generate_presigned_url(file_key)
            except Exception:
                # If presigned URL generation fails, keep the original file_url
                pass
            
            asset_dict = {
                "id": str(created_asset.public_id),
                "asset_type": created_asset.asset_type.value if hasattr(created_asset.asset_type, "value") else created_asset.asset_type,
                "use_for": created_asset.use_for.value if hasattr(created_asset.use_for, "value") else created_asset.use_for,
                "file_url": file_url,
                "title": created_asset.title,
                "is_primary": created_asset.is_primary,
                "sort_order": created_asset.sort_order,
                "status": created_asset.status.value if hasattr(created_asset.status, "value") else created_asset.status,
            }
            created_assets.append(asset_dict)
            
            # Separate by use_for
            if use_for == PropertyAssetUseFor.GALLERY:
                gallery_images.append(asset_dict)
            elif use_for == PropertyAssetUseFor.FEATURE:
                feature_image = asset_dict
            elif use_for == PropertyAssetUseFor.COVER:
                cover_image = asset_dict

        return {
            "assets": created_assets,
            "gallery_images": gallery_images,
            "feature_image": feature_image,
            "cover_image": cover_image,
        }
