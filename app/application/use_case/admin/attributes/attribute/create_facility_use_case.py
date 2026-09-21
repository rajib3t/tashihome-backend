import copy
from typing import Optional

from app.application.dto.attributes.facility import FacilityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.facility_model import Facility
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class CreateFacilityUseCase(BaseUseCase):
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
        verify_csrf: bool,
        current_user: CurrentUser,
        user_service: Optional[UserService] = None,
    ):
        self.facility_service = facility_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user
        self.user_service = user_service

    async def execute(self, facility_dto: FacilityDTO) -> Facility:
        payload = {
            "name": facility_dto.name,
            "icon": facility_dto.icon,
        }

        target_vendor_id = None
        target_vendor = None
        if facility_dto.vendor_id and str(facility_dto.vendor_id).strip():
            raw_vid = str(facility_dto.vendor_id).strip()
            if self.user_service:
                target_vendor = await self.user_service.get_user_by_public_id(raw_vid, flush=True)
                if not target_vendor and raw_vid.isdigit():
                    target_vendor = await self.user_service.get_user_by_id(int(raw_vid), flush=True)
                if not target_vendor:
                    raise AppException(
                        status_code=404,
                        message="Vendor not found.",
                        error_code="VENDOR_NOT_FOUND",
                        field="vendor_id",
                    )
                target_vendor_id = target_vendor.id
            elif raw_vid.isdigit():
                target_vendor_id = int(raw_vid)
            else:
                target_vendor_id = raw_vid

        if await self.facility_service.get_by_name_and_vendor(payload["name"].lower(), vendor_id=None):
            raise AppException(
                status_code=409,
                message="A facility with this name already exists as a global attribute.",
                error_code="FACILITY_ALREADY_EXISTS_GLOBAL",
                field="name",
            )

        if target_vendor_id is not None and await self.facility_service.get_by_name_and_vendor(
            payload["name"].lower(), vendor_id=target_vendor_id
        ):
            raise AppException(
                status_code=409,
                message="This vendor already has a facility with this name.",
                error_code="FACILITY_ALREADY_EXISTS_VENDOR",
                field="name",
            )

        if self._is_upload_file(payload.get("icon")):
            payload["icon"] = await self._upload_file(
                payload["icon"], folder="attributes", field_name="icon"
            )

        facility_obj = Facility(
            name=payload["name"],
            icon_url=payload["icon"],
            vendor_id=target_vendor_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        if target_vendor:
            facility_obj.vendor = target_vendor

        return await self.facility_service.create(facility_obj, commit=True)
