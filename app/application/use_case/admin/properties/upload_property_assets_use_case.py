from fastapi import UploadFile

from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.property_asset_model import PropertyAsset, PropertyAssetType
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
        files: list[UploadFile],
        primary_index: int = 0,
    ) -> list[PropertyAsset]:
        property_ = await self.property_service.get_by_public_id(property_id, flush=True)
        if not property_:
            raise AppException(
                status_code=404,
                message="Property not found.",
                field="property_id",
                error_code="PROPERTY_NOT_FOUND",
            )

        if not files:
            raise AppException(
                status_code=400,
                message="At least one file is required.",
                field="files",
                error_code="INVALID_FILE",
            )

        created_assets: list[PropertyAsset] = []
        for index, upload in enumerate(files):
            file_key = await self._upload_file(
                upload,
                folder=f"properties/{property_.public_id}",
                field_name="files",
                webp=True,
            )
            asset = PropertyAsset(
                property_id=property_.id,
                asset_type=PropertyAssetType.IMAGE,
                file_url=file_key,
                title=upload.filename,
                is_primary=index == primary_index,
                sort_order=index,
                created_by=self.current_user.id,
                updated_by=self.current_user.id,
            )
            created_assets.append(await self.property_asset_service.create(asset, commit=True))

        return created_assets
