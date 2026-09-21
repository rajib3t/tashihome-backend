from app.application.dto.attributes.facility import FacilityQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.facility_model import Facility, FacilityStatus
from app.repositories.base_repository import Page
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
import copy


class ListFacilitiesUseCase(BaseUseCase):

    def __init__(
        self,
        facility_service: FacilityService,
        storage_service: StorageService,
        verify_csrf: bool,
        current_user: CurrentUser,
        user_service: UserService | None = None,
    ):
        self.facility_service = facility_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user
        self.user_service = user_service

    async def execute(
        self,
        request_dto: FacilityQueryDTO,
    ) -> Page[Facility]:
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
            filters.append({"name": "status", "value": FacilityStatus.ACTIVE})
        elif normalized_status == "inactive":
            filters.append({"name": "status", "value": FacilityStatus.INACTIVE})

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

        facilities_page = await self.facility_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            search=request_dto.name,
            filters=filters,
            vendor_id=target_vendor_id,
            scope=scope,
            flush=True
        )

        return facilities_page
