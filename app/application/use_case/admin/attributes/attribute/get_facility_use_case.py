from app.application.dto.attributes.facility import FacilityQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.facility_model import Facility, FacilityStatus
from app.repositories.base_repository import Page
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService
import copy


class ListFacilitiesUseCase(BaseUseCase):

    def __init__(
        self,
        facility_service: FacilityService,
        storage_service: StorageService,
        current_user: CurrentUser,
    ):
        self.facility_service = facility_service
        self.storage_service = storage_service
        self.current_user = current_user

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
        facilities_page = await self.facility_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            search=request_dto.name,
            filters=filters,
            flush=True
        )

        updated_items = []
        for facility in facilities_page.items:
            display_facility = copy.copy(facility)
            if facility.icon_url:
                display_facility.icon_url = facility.icon_url
            updated_items.append(display_facility)

        facilities_page.items = updated_items

        return facilities_page
