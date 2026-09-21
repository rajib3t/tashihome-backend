import copy
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.facility_model import Facility, FacilityStatus
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService


class VendorUpdateFacilityStatusUseCase(BaseUseCase):
    def __init__(
        self,
        facility_service: FacilityService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.facility_service = facility_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, facility_id: str, status: str) -> Facility:
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
                message="You do not have permission to update this facility status.",
                error_code="FACILITY_FORBIDDEN",
                field="facility_id",
            )

        normalized_status = status.strip().lower()
        if normalized_status not in ["active", "inactive"]:
            raise AppException(
                status_code=422,
                message="Status must be either 'active' or 'inactive'.",
                field="status",
                error_code="STATUS_INVALID",
            )

        existing_facility.status = (
            FacilityStatus.ACTIVE
            if normalized_status == "active"
            else FacilityStatus.INACTIVE
        )
        existing_facility.updated_by = self.current_user.id

        facility = await self.facility_service.update(existing_facility, commit=True)
        if facility.icon_url:
            display_facility = copy.copy(facility)
            display_facility.icon_url = facility.icon_url
            return display_facility
        return facility

