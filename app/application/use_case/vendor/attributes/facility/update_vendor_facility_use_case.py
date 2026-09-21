import copy
from app.application.dto.attributes.facility import FacilityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.facility_model import Facility
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService


class VendorUpdateFacilityUseCase(BaseUseCase):
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

        if existing_facility.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You do not have permission to edit this facility.",
                error_code="FACILITY_FORBIDDEN",
                field="facility_id",
            )

        normalized_name = facility_dto.name.strip()

        # Cannot conflict with global
        if await self.facility_service.get_by_name_and_vendor(normalized_name.lower(), vendor_id=None):
            raise AppException(
                status_code=409,
                message="A facility with this name already exists as a global attribute.",
                error_code="FACILITY_ALREADY_EXISTS_GLOBAL",
                field="name",
            )

        # Cannot conflict with another of vendor's facilities
        dup = await self.facility_service.get_by_name_and_vendor(
            normalized_name.lower(), vendor_id=self.current_user.id
        )
        if dup and dup.id != existing_facility.id:
            raise AppException(
                status_code=409,
                message="You already have a facility with this name.",
                error_code="FACILITY_ALREADY_EXISTS_VENDOR",
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

        existing_facility.name = normalized_name
        existing_facility.icon_url = icon_url
        existing_facility.updated_by = self.current_user.id

        return await self.facility_service.update(existing_facility, commit=True)

