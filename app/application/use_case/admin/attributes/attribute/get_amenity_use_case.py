from app.application.dto.attributes.amenity import AmenityQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.amenity_model import Amenity, AmenityStatus
from app.repositories.base_repository import Page
from app.services.amenity_service import AmenityService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
import copy


class ListAmenitiesUseCase(BaseUseCase):
    def __init__(
        self,
        amenity_service: AmenityService,
        storage_service: StorageService,
        current_user: CurrentUser,
        user_service: UserService | None = None,
    ):
        self.amenity_service = amenity_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.user_service = user_service

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

        target_vendor_id: int | None = None
        if request_dto.vendor_id and str(request_dto.vendor_id).strip():
            raw_vid = str(request_dto.vendor_id).strip()
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

        scope = request_dto.scope
        if not scope:
            if target_vendor_id is not None:
                scope = "vendor_combined"
            else:
                scope = "all"

        amenities_page = await self.amenity_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            search=request_dto.name,
            filters=filters,
            vendor_id=target_vendor_id,
            scope=scope,
            flush=True,
        )

        return amenities_page
