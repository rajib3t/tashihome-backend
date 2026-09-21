import copy
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.amenity_model import Amenity, AmenityStatus
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService


class VendorUpdateAmenityStatusUseCase(BaseUseCase):
    def __init__(
        self,
        amenity_service: AmenityService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.amenity_service = amenity_service
        self.storage_service = storage_service
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

        if existing_amenity.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You do not have permission to update this amenity status.",
                error_code="AMENITY_FORBIDDEN",
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
            display_amenity = copy.copy(amenity)
            display_amenity.icon_url = amenity.icon_url
            return display_amenity
        return amenity

