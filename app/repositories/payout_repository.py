from datetime import date, datetime
from typing import Any, Dict, List, Optional, TypedDict

from sqlalchemy import func, or_, select

from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.payout_model import Payout, PayoutStatus
from app.models.property_model import Property
from app.models.user_model import User
from app.repositories.base_repository import BaseRepository, Page


class PayoutWithRelations(TypedDict, total=False):
    vendor: bool
    bank_account: bool
    creator: bool


class PayoutRepository(BaseRepository[Payout]):
    _relation_map = {
        "vendor": Payout.vendor,
        "bank_account": Payout.bank_account,
        "creator": Payout.creator,
    }

    async def create(
        self,
        payout: Payout,
        with_relations: Optional[PayoutWithRelations] = None,
        commit: bool = True,
    ) -> Payout:
        self.db.add(payout)
        if commit:
            await self.db.commit()
            await self.db.refresh(payout)
        if with_relations:
            query = self._apply_relations(
                select(Payout).where(Payout.id == payout.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return payout

    async def get_by_id(
        self,
        payout_id: int,
        with_relations: Optional[PayoutWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Payout]:
        query = select(Payout).where(Payout.id == payout_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[PayoutWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Payout]:
        query = select(Payout).where(Payout.public_id == public_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def get_by_razorpay_payout_id(
        self,
        razorpay_payout_id: str,
        with_relations: Optional[PayoutWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Payout]:
        query = select(Payout).where(Payout.razorpay_payout_id == razorpay_payout_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def update(
        self,
        payout: Payout,
        with_relations: Optional[PayoutWithRelations] = None,
        commit: bool = True,
    ) -> Payout:
        self.db.add(payout)
        if commit:
            await self.db.commit()
            await self.db.refresh(payout)
        if with_relations:
            query = self._apply_relations(
                select(Payout).where(Payout.id == payout.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return payout

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 10,
        vendor_id: Optional[int] = None,
        status: Optional[str] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        sort_order: str = "desc",
        with_relations: Optional[PayoutWithRelations] = None,
        flush: bool = False,
    ) -> Page[Payout]:
        """Paginated list of all payouts for admin."""
        query = select(Payout)

        if vendor_id:
            query = query.where(Payout.vendor_id == vendor_id)

        if status:
            try:
                status_enum = PayoutStatus(status)
                query = query.where(Payout.status == status_enum)
            except ValueError:
                pass

        if period_start:
            query = query.where(Payout.period_end >= period_start)
        if period_end:
            query = query.where(Payout.period_start <= period_end)

        if sort_order.lower() == "asc":
            query = query.order_by(Payout.created_at.asc())
        else:
            query = query.order_by(Payout.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def calculate_vendor_earnings_summary(
        self,
        vendor_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        commission_percentage: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Calculates eligible booking revenue, commission, previous payouts, and net dues for a vendor.
        """
        # Query completed bookings for vendor's properties
        booking_query = (
            select(
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_amount), 0).label("total_gross_amount"),
            )
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                Booking.status.in_([BookingStatus.COMPLETED, BookingStatus.CHECKED_OUT]),
                Booking.payment_status == PaymentStatus.PAID,
            )
        )

        if period_start:
            booking_query = booking_query.where(Booking.check_out_date >= period_start)
        if period_end:
            booking_query = booking_query.where(Booking.check_out_date <= period_end)

        booking_res = await self.db.execute(booking_query)
        total_bookings, total_gross = booking_res.one()
        gross_float = float(total_gross)

        # Calculate platform commission
        commission_amount = round(gross_float * (commission_percentage / 100.0), 2)
        net_payable_potential = round(gross_float - commission_amount, 2)

        # Query existing payouts already paid or in processing
        payout_query = (
            select(
                func.coalesce(func.sum(Payout.amount), 0).label("total_disbursed"),
                func.coalesce(
                    func.sum(
                        case=None
                    ),
                    0
                )
            )
            .where(
                Payout.vendor_id == vendor_id,
                Payout.status.in_([PayoutStatus.PAID, PayoutStatus.PROCESSING]),
            )
        )
        if period_start:
            payout_query = payout_query.where(Payout.period_end >= period_start)
        if period_end:
            payout_query = payout_query.where(Payout.period_start <= period_end)

        payout_res = await self.db.execute(
            select(func.coalesce(func.sum(Payout.amount), 0))
            .where(
                Payout.vendor_id == vendor_id,
                Payout.status.in_([PayoutStatus.PAID, PayoutStatus.PROCESSING]),
            )
        )
        total_disbursed = float(payout_res.scalar_one())

        remaining_due = max(0.0, round(net_payable_potential - total_disbursed, 2))

        return {
            "vendor_id": vendor_id,
            "period_start": period_start,
            "period_end": period_end,
            "completed_bookings_count": total_bookings,
            "gross_booking_amount": gross_float,
            "commission_percentage": commission_percentage,
            "commission_amount": commission_amount,
            "net_earned_amount": net_payable_potential,
            "already_disbursed_amount": total_disbursed,
            "pending_payable_amount": remaining_due,
        }

