from app.application.dto.attributes.amenity import AmenityQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.amenity_model import Amenity, AmenityStatus
from app.repositories.base_repository import Page
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService
import copy


class ListAmenitiesUseCase(BaseUseCase):
    def __init__(
        self,
        amenity_service: AmenityService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.amenity_service = amenity_service
        self.storage_service = storage_service
        self.current_user = current_user

    async def execute(self, request_dto: AmenityQueryDTO) -> Page[Amenity]:
        filters = list(request_dto.filters or [])

        if request_dto.name:
            filters.append({"name": "name", "value": request_dto.name})
        if request_dto.status:
            normalized_status = request_dto.status.strip().lower()
            if normalized_status not in ["active", "inactive"]:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active' or 'inactive'.",
                    field="status",
                    error_code="STATUS_INVALID",
                )
        else:
            normalized_status = None

        if normalized_status == "active":
            filters.append({"name": "status", "value": AmenityStatus.ACTIVE})
        elif normalized_status == "inactive":
            filters.append({"name": "status", "value": AmenityStatus.INACTIVE})
        amenities_page = await self.amenity_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            search=request_dto.name,
            filters=filters,
            flush=True,
        )

        updated_items = []
        for amenity in amenities_page.items:
            display_amenity = copy.copy(amenity)
            if amenity.icon_url:
                display_amenity.icon_url = await self.storage_service.get_display_url(amenity.icon_url)
            updated_items.append(display_amenity)

        amenities_page.items = updated_items

        return amenities_page
