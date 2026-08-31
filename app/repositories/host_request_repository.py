from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import selectinload

from app.models.host_request_message_model import HostRequestMessage
from app.models.host_request_model import HostRequest, HostRequestStatus
from app.repositories.base_repository import BaseRepository, Page


class HostRequestRepository(BaseRepository[HostRequest]):
    async def get_by_public_id(
        self,
        public_id: str | UUID,
        with_messages: bool = True,
        flush: bool = False,
    ) -> Optional[HostRequest]:
        query = select(HostRequest).where(HostRequest.public_id == public_id)
        if with_messages:
            query = query.options(selectinload(HostRequest.messages))
        return await self._fetch_one(query, flush=flush)

    async def get_by_id(
        self,
        request_id: int,
        with_messages: bool = True,
        flush: bool = False,
    ) -> Optional[HostRequest]:
        query = select(HostRequest).where(HostRequest.id == request_id)
        if with_messages:
            query = query.options(selectinload(HostRequest.messages))
        return await self._fetch_one(query, flush=flush)

    async def get_pending_or_review_by_email(
        self,
        email: str,
        flush: bool = False,
    ) -> Optional[HostRequest]:
        query = select(HostRequest).where(
            func.lower(HostRequest.email) == email.strip().lower(),
            HostRequest.status.in_([HostRequestStatus.PENDING, HostRequestStatus.UNDER_REVIEW]),
        )
        return await self._fetch_one(query, flush=flush)

    async def list_requests(
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
        query = select(HostRequest).options(selectinload(HostRequest.messages))

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    HostRequest.full_name.ilike(term),
                    HostRequest.email.ilike(term),
                    HostRequest.phone.ilike(term),
                    HostRequest.company_name.ilike(term),
                    HostRequest.property_name.ilike(term),
                    HostRequest.city.ilike(term),
                )
            )

        if status and status.strip():
            query = query.where(HostRequest.status == status.strip().lower())

        if city and city.strip():
            query = query.where(HostRequest.city.ilike(f"%{city.strip()}%"))

        if email and email.strip():
            query = query.where(func.lower(HostRequest.email) == email.strip().lower())

        if phone and phone.strip():
            query = query.where(HostRequest.phone == phone.strip())

        allowed_fields = {
            "status": HostRequest.status,
            "city": HostRequest.city,
            "property_type": HostRequest.property_type,
        }
        query = self._apply_dynamic_filters(query, filters, allowed_fields)

        # Sorting
        sort_column = getattr(HostRequest, sort_by, HostRequest.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def create(
        self,
        host_request: HostRequest,
        commit: bool = True,
    ) -> HostRequest:
        self.db.add(host_request)
        if not commit:
            return host_request
        await self.db.commit()
        await self.db.refresh(host_request)
        return host_request

    async def update(
        self,
        host_request: HostRequest,
        commit: bool = True,
    ) -> HostRequest:
        if not commit:
            return host_request
        await self.db.commit()
        await self.db.refresh(host_request)
        return host_request

    async def add_message(
        self,
        message: HostRequestMessage,
        commit: bool = True,
    ) -> HostRequestMessage:
        self.db.add(message)
        if not commit:
            return message
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(
        self,
        host_request_id: int,
        include_internal: bool = True,
        flush: bool = False,
    ) -> list[HostRequestMessage]:
        query = select(HostRequestMessage).where(
            HostRequestMessage.host_request_id == host_request_id
        )
        if not include_internal:
            query = query.where(HostRequestMessage.is_internal.is_(False))
        query = query.order_by(HostRequestMessage.created_at.asc())
        return await self._fetch_all(query, flush=flush)

