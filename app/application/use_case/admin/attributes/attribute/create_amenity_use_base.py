from app.application.dto.attributes.amenity import AmenityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.amenity_model import Amenity
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService


class CreateAmenityUseCase(BaseUseCase):
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
            "name": amenity_dto.name,
            "icon": amenity_dto.icon,
        }

        if await self.amenity_service.get_by_name(payload["name"].lower()):
            raise AppException(
                status_code=409,
                message="Amenity already exists",
                error_code="AMENITY_ALREADY_EXISTS",
                field="name",
            )

        if self._is_upload_file(payload.get("icon")):
            payload["icon"] = await self._upload_file(
                payload["icon"], folder="attributes", field_name="icon"
            )

        amenity_obj = Amenity(
            name=payload["name"],
            icon_url=payload["icon"],
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        amenity = await self.amenity_service.create(amenity_obj, commit=True)

        if amenity.icon_url:
            amenity.icon_url = await self.storage_service.get_display_url(amenity.icon_url)

        return amenity
