from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.refund_request_model import RefundRequest, RefundRequestStatus
from app.repositories.base_repository import BaseRepository, Page


class RefundRequestWithRelations(TypedDict, total=False):
    booking: bool
    payment: bool
    requester: bool
    approver: bool


class RefundRequestRepository(BaseRepository[RefundRequest]):
    _relation_map = {
        "booking": RefundRequest.booking,
        "payment": RefundRequest.payment,
        "requester": RefundRequest.requester,
        "approver": RefundRequest.approver,
    }

    async def create(
        self,
        refund_request: RefundRequest,
        with_relations: Optional[RefundRequestWithRelations] = None,
        commit: bool = True,
    ) -> RefundRequest:
        self.db.add(refund_request)
        if commit:
            await self.db.commit()
            await self.db.refresh(refund_request)
        if with_relations:
            query = self._apply_relations(
                select(RefundRequest).where(RefundRequest.id == refund_request.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return refund_request

    async def get_by_id(
        self,
        refund_request_id: int,
        with_relations: Optional[RefundRequestWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RefundRequest]:
        query = select(RefundRequest).where(RefundRequest.id == refund_request_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[RefundRequestWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RefundRequest]:
        query = select(RefundRequest).where(RefundRequest.public_id == public_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def list_by_booking_id(
        self,
        booking_id: int,
        with_relations: Optional[RefundRequestWithRelations] = None,
        flush: bool = False,
    ) -> list[RefundRequest]:
        query = (
            select(RefundRequest)
            .where(RefundRequest.booking_id == booking_id)
            .order_by(RefundRequest.created_at.desc())
        )
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_all(query, flush=flush)

    async def update(
        self,
        refund_request: RefundRequest,
        with_relations: Optional[RefundRequestWithRelations] = None,
        commit: bool = True,
    ) -> RefundRequest:
        self.db.add(refund_request)
        if commit:
            await self.db.commit()
            await self.db.refresh(refund_request)
        if with_relations:
            query = self._apply_relations(
                select(RefundRequest).where(RefundRequest.id == refund_request.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return refund_request

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        booking_id: Optional[int] = None,
        sort_order: str = "desc",
        with_relations: Optional[RefundRequestWithRelations] = None,
        flush: bool = False,
    ) -> Page[RefundRequest]:
        """Paginated list of all refund requests — for admin use."""
        query = select(RefundRequest)

        if status:
            try:
                status_enum = RefundRequestStatus(status)
                query = query.where(RefundRequest.status == status_enum)
            except ValueError:
                pass

        if booking_id:
            query = query.where(RefundRequest.booking_id == booking_id)

        if sort_order.lower() == "asc":
            query = query.order_by(RefundRequest.created_at.asc())
        else:
            query = query.order_by(RefundRequest.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

