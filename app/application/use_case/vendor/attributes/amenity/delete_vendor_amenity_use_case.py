from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService


class VendorDeleteAmenityUseCase(BaseUseCase):
    def __init__(
        self,
        amenity_service: AmenityService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.amenity_service = amenity_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, amenity_id: str) -> None:
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
                message="You do not have permission to delete this amenity.",
                error_code="AMENITY_FORBIDDEN",
                field="amenity_id",
            )

        if existing_amenity.icon_url:
            try:
                await self.storage_service.delete_object(existing_amenity.icon_url)
            except Exception:
                pass

        await self.amenity_service.delete(existing_amenity, commit=True)

