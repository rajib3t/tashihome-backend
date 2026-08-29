from typing import Optional

from sqlalchemy import select

from app.models.refund_request_model import RefundRequest, RefundRequestStatus
from app.repositories.base_repository import BaseRepository


class RefundRequestRepository(BaseRepository[RefundRequest]):
    async def create(self, refund_request: RefundRequest, commit: bool = True) -> RefundRequest:
        self.db.add(refund_request)
        if commit:
            await self.db.commit()
            await self.db.refresh(refund_request)
        return refund_request

    async def get_by_id(self, refund_request_id: int, flush: bool = False) -> Optional[RefundRequest]:
        query = select(RefundRequest).where(RefundRequest.id == refund_request_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Optional[RefundRequest]:
        query = select(RefundRequest).where(RefundRequest.public_id == public_id)
        return await self._fetch_one(query, flush=flush)

    async def list_by_booking_id(self, booking_id: int, flush: bool = False) -> list[RefundRequest]:
        query = (
            select(RefundRequest)
            .where(RefundRequest.booking_id == booking_id)
            .order_by(RefundRequest.created_at.desc())
        )
        return await self._fetch_all(query, flush=flush)

    async def update(self, refund_request: RefundRequest, commit: bool = True) -> RefundRequest:
        self.db.add(refund_request)
        if commit:
            await self.db.commit()
            await self.db.refresh(refund_request)
        return refund_request

