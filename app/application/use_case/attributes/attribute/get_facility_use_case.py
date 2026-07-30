from app.application.dto.attributes.facility import FacilityQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.facility_model import Facility, FacilityStatus
from app.repositories.base_repository import Page
from app.services.facility_service import FacilityService
from app.services.storage_service import StorageService


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
            if request_dto.status not in ["active", "inactive"]:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active' or 'inactive'.",
                    field="status",
                    error_code="STATUS_INVALID",
                )
        if request_dto.status == "active":
            filters.append({"name": "status", "value": FacilityStatus.ACTIVE})
        elif request_dto.status == "inactive":
            filters.append({"name": "status", "value": FacilityStatus.INACTIVE})
        facilities_page = await self.facility_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            search=request_dto.name,
            filters=filters,
            flush=True
        )

        for facility in facilities_page.items:
            if facility.icon_url:
                facility.icon_url = self.storage_service.generate_presigned_url(facility.icon_url)

        return facilities_page