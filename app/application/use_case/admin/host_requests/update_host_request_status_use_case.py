from datetime import datetime, timezone

from app.application.dto.host_requests.host_request import UpdateHostRequestStatusDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.host_request_message_model import HostRequestMessage
from app.models.host_request_model import HostRequestStatus
from app.schemas.host_request_schema import HostRequestResponseData
from app.services.host_request_service import HostRequestService
from app.services.user_service import UserService


class UpdateHostRequestStatusUseCase(BaseUseCase):
    def __init__(
        self,
        host_request_service: HostRequestService,
        user_service: UserService,
        current_user: CurrentUser,
    ):
        self.host_request_service = host_request_service
        self.user_service = user_service
        self.current_user = current_user

    async def execute(
        self,
        request_id: str,
        data: UpdateHostRequestStatusDTO,
    ) -> HostRequestResponseData:
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

        if host_request.status == HostRequestStatus.CONVERTED:
            raise AppException(
                status_code=400,
                message="Cannot modify status of a request that has already been converted.",
                error_code="REQUEST_ALREADY_CONVERTED",
                field="status",
            )

        valid_statuses = [
            HostRequestStatus.PENDING.value,
            HostRequestStatus.UNDER_REVIEW.value,
            HostRequestStatus.APPROVED.value,
            HostRequestStatus.REJECTED.value,
        ]

        normalized_status = data.status.strip().lower()
        if normalized_status not in valid_statuses:
            raise AppException(
                status_code=422,
                message=f"Invalid status value. Allowed status values: {', '.join(valid_statuses)}.",
                field="status",
                error_code="STATUS_INVALID",
            )

        admin_user = await self.user_service.get_user_by_id(self.current_user.id)
        admin_name = admin_user.full_name if admin_user and admin_user.full_name else "Administrator"

        session = self.host_request_service.host_request_repository.db
        tx = session.begin_nested() if session.in_transaction() else session.begin()

        async with tx:
            host_request.status = HostRequestStatus(normalized_status)
            host_request.reviewed_by = self.current_user.id
            host_request.reviewed_at = datetime.now(timezone.utc)

            await self.host_request_service.update(host_request, commit=False)

            if data.notes and data.notes.strip():
                status_msg = HostRequestMessage(
                    host_request_id=host_request.id,
                    sender_id=self.current_user.id,
                    sender_name=admin_name,
                    sender_role="admin",
                    message=f"[Status changed to '{normalized_status}'] {data.notes.strip()}",
                    is_internal=True,
                )
                await self.host_request_service.add_message(status_msg, commit=False)

            await session.flush()

        reloaded = await self.host_request_service.get_by_id(host_request.id, with_messages=True, flush=True)
        return self.host_request_service.build_host_request_response(
            reloaded or host_request,
            include_internal_messages=True,
        )

