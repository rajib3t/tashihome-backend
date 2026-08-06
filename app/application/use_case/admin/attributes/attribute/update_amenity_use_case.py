from app.application.dto.attributes.amenity import AmenityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.amenity_model import Amenity, AmenityStatus
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService


class UpdateAmenityUseCase(BaseUseCase):
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

        duplicate_name = await self.amenity_service.get_by_name(
            name=amenity_dto.name.lower(),
            flush=False,
        )
        if duplicate_name and duplicate_name.id != existing_amenity.id:
            raise AppException(
                status_code=409,
                message="Amenity already exists",
                error_code="AMENITY_ALREADY_EXISTS",
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

        existing_amenity.name = amenity_dto.name
        existing_amenity.icon_url = icon_url
        existing_amenity.updated_by = self.current_user.id

        amenity = await self.amenity_service.update(existing_amenity, commit=True)
        if amenity.icon_url:
            amenity.icon_url = await self.storage_service.get_display_url(amenity.icon_url)

        return amenity


class UpdateStatusAmenityUseCase(BaseUseCase):
    def __init__(
        self,
        amenity_service: AmenityService,
        current_user: CurrentUser,
    ):
        self.amenity_service = amenity_service
        self.current_user = current_user

    async def execute(self, amenity_id: str, status: str) -> Amenity:
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

        normalized_status = status.strip().lower()
        if normalized_status not in ["active", "inactive"]:
            raise AppException(
                status_code=422,
                message="Status must be either 'active' or 'inactive'.",
                field="status",
                error_code="STATUS_INVALID",
            )

        existing_amenity.status = (
            AmenityStatus.ACTIVE
            if normalized_status == "active"
            else AmenityStatus.INACTIVE
        )
        existing_amenity.updated_by = self.current_user.id

        amenity = await self.amenity_service.update(existing_amenity, commit=True)
        if amenity.icon_url:
            amenity.icon_url = await self.storage_service.get_display_url(amenity.icon_url)
        return amenity
