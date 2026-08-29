from typing import Optional

from app.models.refund_request_model import RefundRequest
from app.repositories.refund_request_repository import RefundRequestRepository


class RefundRequestService:
    def __init__(self, refund_request_repository: RefundRequestRepository):
        self.refund_request_repository = refund_request_repository

    async def create(self, refund_request: RefundRequest, commit: bool = True) -> RefundRequest:
        return await self.refund_request_repository.create(refund_request, commit=commit)

    async def get_by_id(self, refund_request_id: int, flush: bool = False) -> Optional[RefundRequest]:
        return await self.refund_request_repository.get_by_id(refund_request_id, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Optional[RefundRequest]:
        return await self.refund_request_repository.get_by_public_id(public_id, flush=flush)

    async def list_by_booking_id(self, booking_id: int, flush: bool = False) -> list[RefundRequest]:
        return await self.refund_request_repository.list_by_booking_id(booking_id, flush=flush)

    async def update(self, refund_request: RefundRequest, commit: bool = True) -> RefundRequest:
        return await self.refund_request_repository.update(refund_request, commit=commit)

