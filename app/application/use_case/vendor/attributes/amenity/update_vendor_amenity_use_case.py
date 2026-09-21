import copy
from app.application.dto.attributes.amenity import AmenityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.amenity_model import Amenity
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService


class VendorUpdateAmenityUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "icon": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg"),
            "max_size_bytes": 500 * 1024,
        },
    }

    def __init__(
        self,
        amenity_service: AmenityService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.amenity_service = amenity_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, amenity_id: str, amenity_dto: AmenityDTO) -> Amenity:
        existing_amenity = await self.amenity_service.get_by_public_id(
            public_id=amenity_id, flush=False
        )
        if not existing_amenity:
            raise AppException(
                status_code=404,
                message="Amenity not found",
                error_code="AMENITY_NOT_FOUND",
                field="amenity_id",
            )

        if existing_amenity.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You do not have permission to edit this amenity.",
                error_code="AMENITY_FORBIDDEN",
                field="amenity_id",
            )

        normalized_name = amenity_dto.name.strip()

        # Cannot conflict with global
        if await self.amenity_service.get_by_name_and_vendor(normalized_name.lower(), vendor_id=None):
            raise AppException(
                status_code=409,
                message="An amenity with this name already exists as a global attribute.",
                error_code="AMENITY_ALREADY_EXISTS_GLOBAL",
                field="name",
            )

        # Cannot conflict with another of the vendor's amenities
        dup = await self.amenity_service.get_by_name_and_vendor(
            normalized_name.lower(), vendor_id=self.current_user.id
        )
        if dup and dup.id != existing_amenity.id:
            raise AppException(
                status_code=409,
                message="You already have an amenity with this name.",
                error_code="AMENITY_ALREADY_EXISTS_VENDOR",
                field="name",
            )

        icon_url = amenity_dto.icon
        if self._is_upload_file(icon_url):
            old_icon_url = existing_amenity.icon_url
            icon_url = await self._upload_file(
                icon_url, folder="attributes", field_name="icon"
            )
            if isinstance(old_icon_url, str) and old_icon_url:
                try:
                    await self.storage_service.delete_object(old_icon_url)
                except Exception:
                    pass
        elif icon_url is None:
            icon_url = existing_amenity.icon_url

        existing_amenity.name = normalized_name
        existing_amenity.icon_url = icon_url
        existing_amenity.updated_by = self.current_user.id

        return await self.amenity_service.update(existing_amenity, commit=True)

