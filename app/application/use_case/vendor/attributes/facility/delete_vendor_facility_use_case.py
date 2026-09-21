from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService


class VendorDeleteFacilityUseCase(BaseUseCase):
    def __init__(
        self,
        facility_service: FacilityService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.facility_service = facility_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, facility_id: str) -> None:
        existing_facility = await self.facility_service.get_by_public_id(
            public_id=facility_id, flush=False
        )
        if not existing_facility:
            raise AppException(
                status_code=404,
                message="Facility not found",
                error_code="FACILITY_NOT_FOUND",
                field="facility_id",
            )

        if existing_facility.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You do not have permission to delete this facility.",
                error_code="FACILITY_FORBIDDEN",
                field="facility_id",
            )

        if existing_facility.icon_url:
            try:
                await self.storage_service.delete_object(existing_facility.icon_url)
            except Exception:
                pass

        await self.facility_service.delete(existing_facility, commit=True)

