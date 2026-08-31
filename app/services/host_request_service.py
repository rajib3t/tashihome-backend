from typing import Optional, Sequence
from uuid import UUID

from app.models.host_request_message_model import HostRequestMessage
from app.models.host_request_model import HostRequest
from app.repositories.base_repository import Page
from app.repositories.host_request_repository import HostRequestRepository
from app.schemas.host_request_schema import (
    HostRequestMessageResponseData,
    HostRequestResponseData,
)


class HostRequestService:
    def __init__(self, host_request_repository: HostRequestRepository):
        self.host_request_repository = host_request_repository

    async def get_by_public_id(
        self,
        public_id: str | UUID,
        with_messages: bool = True,
        flush: bool = False,
    ) -> Optional[HostRequest]:
        return await self.host_request_repository.get_by_public_id(
            public_id=public_id,
            with_messages=with_messages,
            flush=flush,
        )

    async def get_by_id(
        self,
        request_id: int,
        with_messages: bool = True,
        flush: bool = False,
    ) -> Optional[HostRequest]:
        return await self.host_request_repository.get_by_id(
            request_id=request_id,
            with_messages=with_messages,
            flush=flush,
        )

    async def get_pending_or_review_by_email(
        self,
        email: str,
        flush: bool = False,
    ) -> Optional[HostRequest]:
        return await self.host_request_repository.get_pending_or_review_by_email(
            email=email,
            flush=flush,
        )

    async def list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
        city: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        filters: Optional[Sequence[dict]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        flush: bool = False,
    ) -> Page[HostRequest]:
        return await self.host_request_repository.list_requests(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            city=city,
            email=email,
            phone=phone,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            flush=flush,
        )

    async def create(
        self,
        host_request: HostRequest,
        commit: bool = True,
    ) -> HostRequest:
        return await self.host_request_repository.create(host_request, commit=commit)

    async def update(
        self,
        host_request: HostRequest,
        commit: bool = True,
    ) -> HostRequest:
        return await self.host_request_repository.update(host_request, commit=commit)

    async def add_message(
        self,
        message: HostRequestMessage,
        commit: bool = True,
    ) -> HostRequestMessage:
        return await self.host_request_repository.add_message(message, commit=commit)

    async def get_messages(
        self,
        host_request_id: int,
        include_internal: bool = True,
        flush: bool = False,
    ) -> list[HostRequestMessage]:
        return await self.host_request_repository.get_messages(
            host_request_id=host_request_id,
            include_internal=include_internal,
            flush=flush,
        )

    @staticmethod
    def build_host_request_response(
        host_request: HostRequest,
        include_internal_messages: bool = True,
    ) -> HostRequestResponseData:
        messages_data = []
        if host_request.messages:
            for msg in host_request.messages:
                if not include_internal_messages and msg.is_internal:
                    continue
                messages_data.append(
                    HostRequestMessageResponseData(
                        id=str(msg.public_id),
                        sender_id=str(msg.sender_id) if msg.sender_id else None,
                        sender_name=msg.sender_name,
                        sender_role=msg.sender_role,
                        message=msg.message,
                        is_internal=msg.is_internal,
                        created_at=msg.created_at,
                    )
                )

        return HostRequestResponseData(
            id=str(host_request.public_id),
            user_id=str(host_request.user_id) if host_request.user_id else None,
            full_name=host_request.full_name,
            email=host_request.email,
            phone=host_request.phone,
            company_name=host_request.company_name,
            property_name=host_request.property_name,
            property_type=host_request.property_type,
            city=host_request.city,
            address=host_request.address,
            expected_rooms=host_request.expected_rooms,
            notes=host_request.notes,
            status=host_request.status,
            reviewed_by=str(host_request.reviewed_by) if host_request.reviewed_by else None,
            reviewed_at=host_request.reviewed_at,
            converted_user_id=str(host_request.converted_user_id) if host_request.converted_user_id else None,
            created_at=host_request.created_at,
            updated_at=host_request.updated_at,
            messages=messages_data,
        )

