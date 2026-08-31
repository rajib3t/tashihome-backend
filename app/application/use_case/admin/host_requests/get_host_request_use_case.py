from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.schemas.host_request_schema import HostRequestResponseData
from app.services.host_request_service import HostRequestService


class GetHostRequestUseCase(BaseUseCase):
    def __init__(
        self,
        host_request_service: HostRequestService,
        current_user: CurrentUser,
    ):
        self.host_request_service = host_request_service
        self.current_user = current_user

    async def execute(self, request_id: str) -> HostRequestResponseData:
        host_request = await self.host_request_service.get_by_public_id(
            public_id=request_id,
            with_messages=True,
            flush=True,
        )
        if not host_request:
            raise AppException(
                status_code=404,
                message="Host request not found",
                error_code="HOST_REQUEST_NOT_FOUND",
                field="request_id",
            )

        return self.host_request_service.build_host_request_response(
            host_request,
            include_internal_messages=True,
        )

