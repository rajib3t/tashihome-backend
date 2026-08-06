from app.application.dto.attributes.facility import  FacilityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser

from app.models.facility_model import Facility
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService


class CreateFacilityUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
            "icon": {
                "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg",),
                "max_size_bytes": 500 * 1024,
            },
        }
    def __init__(self, 
        facility_service : FacilityService,
        storage_service : StorageService,
        verify_csrf : bool ,
        current_user : CurrentUser,
        ):
        self.facility_service = facility_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(self, facility_dto : FacilityDTO) -> Facility:
        payload = {
                    "name": facility_dto.name,
                    "icon": facility_dto.icon,
                }

        if await self.facility_service.get_by_name(payload["name"].lower()):
            raise AppException(
                status_code=409,
                message="Facility already exists",
                error_code="FACILITY_ALREADY_EXISTS",
                field="name",
            )

        if self._is_upload_file(payload.get("icon")):
            payload["icon"] = await self._upload_file(
                payload["icon"], folder="attributes", field_name="icon"
            )

        facility_obj = Facility(
            name=payload["name"],
            icon_url=payload["icon"],
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        facility = await self.facility_service.create(facility_obj, commit=True)

        if facility.icon_url:
            facility.icon_url = await self.storage_service.get_display_url(facility.icon_url)

        return facility
