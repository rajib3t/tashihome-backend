from datetime import date
from typing import Optional, Sequence, TypedDict

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.property_model import Property
from app.repositories.base_repository import BaseRepository, Page


class BookingWithRelations(TypedDict, total=False):
    guest: bool
    property: bool
    room_type: bool
    cancellation_policy: bool
    payments: bool
    refund_requests: bool
    review: bool


class BookingRepository(BaseRepository[Booking]):
    @property
    def _relation_map(self):
        return {
            "guest": selectinload(Booking.guest),
            "property": selectinload(Booking.property)
            .selectinload(Property.property_assets),
            "room_type": selectinload(Booking.room_type),
            "cancellation_policy": selectinload(Booking.cancellation_policy),
            "payments": selectinload(Booking.payments),
            "refund_requests": selectinload(Booking.refund_requests),
            "review": selectinload(Booking.review),
        }

    _filter_map = {
        "guest_id": Booking.guest_id,
        "property_id": Booking.property_id,
        "room_type_id": Booking.room_type_id,
        "status": Booking.status,
        "payment_status": Booking.payment_status,
        "booking_reference": Booking.booking_reference,
        "public_id": Booking.public_id,
    }

    async def create(
        self,
        booking: Booking,
        with_relations: Optional[BookingWithRelations] = None,
        commit: bool = True,
    ) -> Booking:
        self.db.add(booking)
        if commit:
            await self.db.commit()
            await self.db.refresh(booking)
        if with_relations:
            query = self._apply_relations(
                select(Booking).where(Booking.id == booking.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return booking

    async def get_by_id(
        self,
        booking_id: int,
        with_relations: Optional[BookingWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Booking]:
        query = self._apply_relations(
            select(Booking).where(Booking.id == booking_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[BookingWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Booking]:
        query = self._apply_relations(
            select(Booking).where(Booking.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_booking_reference(
        self,
        booking_reference: str,
        with_relations: Optional[BookingWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Booking]:
        query = self._apply_relations(
            select(Booking).where(Booking.booking_reference == booking_reference),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_user_booking_by_identifier(
        self,
        guest_id: int,
        identifier: str,
        with_relations: Optional[BookingWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Booking]:
        """Fetch a booking belonging to `guest_id` by either public_id (UUID) or booking_reference."""
        query = select(Booking).where(Booking.guest_id == guest_id)

        try:
            from uuid import UUID

            uuid_obj = UUID(str(identifier))
            query = query.where(
                or_(
                    Booking.public_id == uuid_obj,
                    Booking.booking_reference == str(identifier),
                )
            )
        except (ValueError, AttributeError):
            query = query.where(Booking.booking_reference == str(identifier))

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def update(
        self,
        booking: Booking,
        with_relations: Optional[BookingWithRelations] = None,
        commit: bool = True,
    ) -> Booking:
        self.db.add(booking)
        if commit:
            await self.db.commit()
            await self.db.refresh(booking)
        if with_relations:
            query = self._apply_relations(
                select(Booking).where(Booking.id == booking.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return booking

    async def delete(self, booking: Booking, commit: bool = True) -> None:
        await self.db.delete(booking)
        if commit:
            await self.db.commit()

    async def list_user_bookings(
        self,
        guest_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        with_relations: Optional[BookingWithRelations] = None,
        flush: bool = False,
    ) -> Page[Booking]:
        query = select(Booking).where(Booking.guest_id == guest_id)

        if status:
            query = query.where(Booking.status == status)

        if payment_status:
            query = query.where(Booking.payment_status == payment_status)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Booking.booking_reference.ilike(search_term),
                    Booking.special_requests.ilike(search_term),
                )
            )

        # Sorting
        sort_column = getattr(Booking, sort_by, Booking.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def count_booked_units(
        self,
        property_id: int,
        room_type_id: Optional[int],
        check_in_date: date,
        check_out_date: date,
        exclude_booking_id: Optional[int] = None,
    ) -> int:
        """
        Count active booked rooms overlapping with the given date range.
        Active statuses: PENDING, CONFIRMED, CHECKED_IN.
        Overlap condition: check_in_date < booking.check_out_date AND check_out_date > booking.check_in_date.
        """
        active_statuses = [
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
            BookingStatus.CHECKED_IN,
        ]

        query = select(func.coalesce(func.sum(Booking.num_rooms), 0)).where(
            and_(
                Booking.property_id == property_id,
                Booking.status.in_(active_statuses),
                Booking.check_in_date < check_out_date,
                Booking.check_out_date > check_in_date,
            )
        )

        if room_type_id is not None:
            query = query.where(Booking.room_type_id == room_type_id)

        if exclude_booking_id is not None:
            query = query.where(Booking.id != exclude_booking_id)

        result = await self.db.execute(query)
        return int(result.scalar_one())

