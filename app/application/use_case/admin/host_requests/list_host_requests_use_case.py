from app.application.dto.host_requests.host_request import HostRequestQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.host_request_model import HostRequestStatus
from app.repositories.base_repository import Page
from app.schemas.host_request_schema import HostRequestResponseData
from app.services.host_request_service import HostRequestService


class ListHostRequestsUseCase(BaseUseCase):
    def __init__(
        self,
        host_request_service: HostRequestService,
        current_user: CurrentUser,
    ):
        self.host_request_service = host_request_service
        self.current_user = current_user

    async def execute(self, params: HostRequestQueryDTO) -> Page[HostRequestResponseData]:
        valid_statuses = [s.value for s in HostRequestStatus]
        if params.status:
            normalized_status = params.status.strip().lower()
            if normalized_status not in valid_statuses:
                raise AppException(
                    status_code=422,
                    message=f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}.",
                    field="status",
                    error_code="STATUS_INVALID",
                )

        filters = []
        if params.filters:
            for f in params.filters:
                filters.append({"name": f.name, "value": f.value})

        page_result = await self.host_request_service.list(
            page=params.page,
            page_size=params.size,
            search=params.search,
            status=params.status,
            city=params.city,
            email=params.email,
            phone=params.phone,
            filters=filters if filters else None,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            flush=True,
        )

        items = [
            self.host_request_service.build_host_request_response(req, include_internal_messages=True)
            for req in page_result.items
        ]

        return Page(
            items=items,
            total=page_result.total,
            page=page_result.page,
            page_size=page_result.page_size,
        )

