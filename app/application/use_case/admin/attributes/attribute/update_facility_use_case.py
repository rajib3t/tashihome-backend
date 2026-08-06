from app.application.dto.attributes.facility import FacilityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.facility_model import Facility, FacilityStatus
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService


class UpdateFacilityUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "icon": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg"),
            "max_size_bytes": 500 * 1024,
        },
    }

    def __init__(
        self,
        facility_service: FacilityService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.facility_service = facility_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, facility_id: str, facility_dto: FacilityDTO) -> Facility:
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

        duplicate_name = await self.facility_service.get_by_name(
            name=facility_dto.name.lower(),
            flush=False,
        )
        if duplicate_name and duplicate_name.id != existing_facility.id:
            raise AppException(
                status_code=409,
                message="Facility already exists",
                error_code="FACILITY_ALREADY_EXISTS",
                field="name",
            )

        icon_url = facility_dto.icon
        if self._is_upload_file(icon_url):
            old_icon_url = existing_facility.icon_url
            icon_url = await self._upload_file(
                icon_url, folder="attributes", field_name="icon"
            )
            if isinstance(old_icon_url, str) and old_icon_url:
                try:
                    await self.storage_service.delete_object(old_icon_url)
                except Exception:
                    pass
        elif icon_url is None:
            icon_url = existing_facility.icon_url

        existing_facility.name = facility_dto.name
        existing_facility.icon_url = icon_url
        existing_facility.updated_by = self.current_user.id

        facility = await self.facility_service.update(existing_facility, commit=True)
        if facility.icon_url:
            facility.icon_url = await self.storage_service.get_display_url(facility.icon_url)

        return facility


class UpdateStatusFacilityUseCase(BaseUseCase):
    def __init__(
        self,
        facility_service: FacilityService,
        current_user: CurrentUser,
    ):
        self.facility_service = facility_service
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
            facility.icon_url = await self.storage_service.get_display_url(facility.icon_url)
        return facility
