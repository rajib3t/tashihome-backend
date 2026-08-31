import logging
from typing import Optional

from app.application.dto.host_requests.host_request import CreateHostRequestDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.host_request_message_model import HostRequestMessage
from app.models.host_request_model import HostRequest, HostRequestStatus
from app.models.user_model import UserRole
from app.schemas.host_request_schema import HostRequestResponseData
from app.services.host_request_service import HostRequestService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class SubmitHostRequestUseCase(BaseUseCase):
    def __init__(
        self,
        host_request_service: HostRequestService,
        user_service: UserService,
    ):
        self.host_request_service = host_request_service
        self.user_service = user_service

    async def execute(self, data: CreateHostRequestDTO) -> HostRequestResponseData:
        normalized_email = data.email.strip().lower()
        normalized_phone = data.phone.strip()

        # 1. Check if an active pending or under_review request already exists
        existing_request = await self.host_request_service.get_pending_or_review_by_email(
            email=normalized_email,
            flush=False,
        )
        if existing_request:
            raise AppException(
                status_code=409,
                message="A host application with this email is already pending review.",
                error_code="PENDING_REQUEST_EXISTS",
                field="email",
            )

        # 2. Check if user already exists and is already a vendor
        existing_user = await self.user_service.get_user_by_email(
            email=normalized_email,
            flush=False,
        )
        user_id = None
        if existing_user:
            if existing_user.role == UserRole.VENDOR:
                raise AppException(
                    status_code=400,
                    message="You are already registered as a host.",
                    error_code="ALREADY_A_HOST",
                    field="email",
                )
            user_id = existing_user.id

        session = self.host_request_service.host_request_repository.db
        tx = session.begin_nested() if session.in_transaction() else session.begin()

        async with tx:
            host_request = HostRequest(
                user_id=user_id,
                full_name=data.full_name.strip(),
                email=normalized_email,
                phone=normalized_phone,
                company_name=data.company_name.strip() if data.company_name else None,
                property_name=data.property_name.strip() if data.property_name else None,
                property_type=data.property_type.strip() if data.property_type else None,
                city=data.city.strip() if data.city else None,
                address=data.address.strip() if data.address else None,
                expected_rooms=data.expected_rooms,
                notes=data.notes.strip() if data.notes else None,
                status=HostRequestStatus.PENDING,
            )
            created_request = await self.host_request_service.create(host_request, commit=False)
            await session.flush()

            # If applicant left notes, record initial message in the conversation thread
            if data.notes and data.notes.strip():
                init_msg = HostRequestMessage(
                    host_request_id=created_request.id,
                    sender_id=user_id,
                    sender_name=data.full_name.strip(),
                    sender_role="applicant",
                    message=data.notes.strip(),
                    is_internal=False,
                )
                await self.host_request_service.add_message(init_msg, commit=False)
                await session.flush()

        # Reload with messages
        reloaded = await self.host_request_service.get_by_id(created_request.id, with_messages=True, flush=True)
        return self.host_request_service.build_host_request_response(reloaded or created_request)

