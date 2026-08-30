from typing import Optional

from app.models.refund_request_model import RefundRequest
from app.repositories.base_repository import Page
from app.repositories.refund_request_repository import (
    RefundRequestRepository,
    RefundRequestWithRelations,
)


class RefundRequestService:
    def __init__(self, refund_request_repository: RefundRequestRepository):
        self.refund_request_repository = refund_request_repository

    async def create(
        self,
        refund_request: RefundRequest,
        with_relations: Optional[RefundRequestWithRelations] = None,
        commit: bool = True,
    ) -> RefundRequest:
        return await self.refund_request_repository.create(
            refund_request, with_relations=with_relations, commit=commit
        )

    async def get_by_id(
        self,
        refund_request_id: int,
        with_relations: Optional[RefundRequestWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RefundRequest]:
        return await self.refund_request_repository.get_by_id(
            refund_request_id, with_relations=with_relations, flush=flush
        )

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[RefundRequestWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RefundRequest]:
        return await self.refund_request_repository.get_by_public_id(
            public_id, with_relations=with_relations, flush=flush
        )

    async def list_by_booking_id(
        self,
        booking_id: int,
        with_relations: Optional[RefundRequestWithRelations] = None,
        flush: bool = False,
    ) -> list[RefundRequest]:
        return await self.refund_request_repository.list_by_booking_id(
            booking_id, with_relations=with_relations, flush=flush
        )

    async def update(
        self,
        refund_request: RefundRequest,
        with_relations: Optional[RefundRequestWithRelations] = None,
        commit: bool = True,
    ) -> RefundRequest:
        return await self.refund_request_repository.update(
            refund_request, with_relations=with_relations, commit=commit
        )

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        booking_id: Optional[int] = None,
        sort_order: str = "desc",
        with_relations: Optional[RefundRequestWithRelations] = None,
    ) -> Page[RefundRequest]:
        return await self.refund_request_repository.list_all(
            page=page,
            page_size=page_size,
            status=status,
            booking_id=booking_id,
            sort_order=sort_order,
            with_relations=with_relations,
        )

