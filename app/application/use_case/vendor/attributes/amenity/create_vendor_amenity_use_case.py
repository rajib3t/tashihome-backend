import copy
from app.application.dto.attributes.amenity import AmenityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.amenity_model import Amenity
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService


class VendorCreateAmenityUseCase(BaseUseCase):
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
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.amenity_service = amenity_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(self, amenity_dto: AmenityDTO) -> Amenity:
        payload = {
            "name": amenity_dto.name.strip(),
            "icon": amenity_dto.icon,
        }

        # 1. Vendor cannot create with same name as global
        if await self.amenity_service.get_by_name_and_vendor(payload["name"].lower(), vendor_id=None):
            raise AppException(
                status_code=409,
                message="An amenity with this name already exists as a global attribute.",
                error_code="AMENITY_ALREADY_EXISTS_GLOBAL",
                field="name",
            )

        # 2. Vendor cannot create duplicate within own amenities
        if await self.amenity_service.get_by_name_and_vendor(payload["name"].lower(), vendor_id=self.current_user.id):
            raise AppException(
                status_code=409,
                message="You already have an amenity with this name.",
                error_code="AMENITY_ALREADY_EXISTS_VENDOR",
                field="name",
            )

        if self._is_upload_file(payload.get("icon")):
            payload["icon"] = await self._upload_file(
                payload["icon"], folder="attributes", field_name="icon"
            )

        amenity_obj = Amenity(
            name=payload["name"],
            icon_url=payload["icon"],
            vendor_id=self.current_user.id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        return await self.amenity_service.create(amenity_obj, commit=True)

