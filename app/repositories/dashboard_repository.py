from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import String, and_, case, distinct, func, or_, select

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.city_model import City
from app.models.host_request_model import HostRequest, HostRequestStatus
from app.models.payment_model import Payment, TransactionStatus
from app.models.payout_model import Payout, PayoutStatus
from app.models.property_asset_model import PropertyAsset
from app.models.property_model import Property, PropertyStatus, PropertyType
from app.models.refund_request_model import RefundRequest, RefundRequestStatus
from app.models.review_model import Review, ReviewStatus
from app.models.user_model import User, UserRole, UserStatus


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────────────────────────────────
    # ADMIN REPOSITORY METHODS
    # ──────────────────────────────────────────────────────────────────────────

    async def get_admin_booking_stats(self) -> Dict[str, int]:
        query = select(
            Booking.status,
            func.count(Booking.id).label("count"),
        ).group_by(Booking.status)
        result = await self.db.execute(query)
        rows = result.all()

        stats = {
            "total": 0,
            "pending": 0,
            "confirmed": 0,
            "checked_in": 0,
            "checked_out": 0,
            "cancelled": 0,
            "completed": 0,
            "no_show": 0,
        }

        for status_val, count in rows:
            key = status_val.value if hasattr(status_val, "value") else str(status_val).lower()
            if key in stats:
                stats[key] = count
            stats["total"] += count

        return stats

    async def get_admin_revenue_stats(self) -> Dict[str, Any]:
        # Completed / confirmed / checked-in / checked-out revenue
        revenue_statuses = [
            BookingStatus.CONFIRMED,
            BookingStatus.CHECKED_IN,
            BookingStatus.CHECKED_OUT,
            BookingStatus.COMPLETED,
        ]
        paid_payment_statuses = [
            PaymentStatus.PAID,
            PaymentStatus.PARTIALLY_PAID,
        ]

        # Gross revenue from valid bookings
        rev_query = select(
            func.coalesce(func.sum(Booking.total_amount), 0)
        ).where(
            or_(
                Booking.status.in_(revenue_statuses),
                Booking.payment_status.in_(paid_payment_statuses),
            )
        )
        booking_revenue = (await self.db.execute(rev_query)).scalar_one()

        # Gross revenue from successful payments
        pay_gross_query = select(
            func.coalesce(func.sum(Payment.amount), 0)
        ).where(
            Payment.status.in_([
                TransactionStatus.SUCCESS,
                TransactionStatus.PARTIALLY_REFUNDED,
                TransactionStatus.REFUNDED,
            ])
        )
        pay_gross = (await self.db.execute(pay_gross_query)).scalar_one()

        gross_revenue = max(float(pay_gross or 0.0), float(booking_revenue or 0.0))

        # Pending revenue
        pending_query = select(
            func.coalesce(func.sum(Booking.total_amount), 0)
        ).where(
            and_(
                Booking.status == BookingStatus.PENDING,
                Booking.payment_status == PaymentStatus.PENDING,
            )
        )
        pending_revenue = (await self.db.execute(pending_query)).scalar_one()

        # Refunded amount from refund requests or payment records
        refund_req_query = select(
            func.coalesce(func.sum(RefundRequest.amount), 0)
        ).where(
            or_(
                RefundRequest.status == RefundRequestStatus.PROCESSED,
                RefundRequest.status == RefundRequestStatus.APPROVED,
                func.lower(func.cast(RefundRequest.status, String)).in_(["approved", "processed"]),
            )
        )
        refund_req_amount = (await self.db.execute(refund_req_query)).scalar_one()

        pay_refund_query = select(func.coalesce(func.sum(Payment.refunded_amount), 0))
        pay_refund_amount = (await self.db.execute(pay_refund_query)).scalar_one()

        refunded_amount = max(float(refund_req_amount or 0.0), float(pay_refund_amount or 0.0))
        net_revenue = max(0.0, float(gross_revenue or 0.0) - float(refunded_amount or 0.0))

        return {
            "total_revenue": float(net_revenue or 0.0),
            "gross_revenue": float(gross_revenue or 0.0),
            "net_revenue": float(net_revenue or 0.0),
            "pending_revenue": float(pending_revenue or 0.0),
            "refunded_amount": float(refunded_amount or 0.0),
            "total_refunded": float(refunded_amount or 0.0),
            "currency": "INR",
        }




    async def get_admin_property_stats(self) -> Dict[str, Any]:
        status_query = select(
            Property.status,
            func.count(Property.id).label("count"),
        ).group_by(Property.status)
        status_rows = (await self.db.execute(status_query)).all()

        type_query = select(
            Property.type,
            func.count(Property.id).label("count"),
        ).where(Property.type.isnot(None)).group_by(Property.type)
        type_rows = (await self.db.execute(type_query)).all()

        featured_query = select(
            func.count(Property.id)
        ).where(Property.is_featured.is_(True))
        featured_count = (await self.db.execute(featured_query)).scalar_one()

        stats = {
            "total": 0,
            "active": 0,
            "draft": 0,
            "inactive": 0,
            "archived": 0,
            "featured": int(featured_count or 0),
            "by_type": {},
        }

        for st, count in status_rows:
            key = st.value if hasattr(st, "value") else str(st).lower()
            if key in stats:
                stats[key] = count
            stats["total"] += count

        for pt, count in type_rows:
            if pt is not None:
                pt_key = pt.value if hasattr(pt, "value") else str(pt).lower()
                stats["by_type"][pt_key] = count

        return stats

    async def get_admin_user_stats(self) -> Dict[str, Any]:
        status_query = select(
            User.status,
            func.count(User.id).label("count"),
        ).group_by(User.status)
        status_rows = (await self.db.execute(status_query)).all()

        role_query = select(
            User.role,
            func.count(User.id).label("count"),
        ).group_by(User.role)
        role_rows = (await self.db.execute(role_query)).all()

        pending_hosts_query = select(
            func.count(HostRequest.id)
        ).where(HostRequest.status == HostRequestStatus.PENDING)
        pending_hosts = (await self.db.execute(pending_hosts_query)).scalar_one()

        stats = {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "suspended": 0,
            "by_role": {},
            "pending_hosts": int(pending_hosts or 0),
        }

        for st, count in status_rows:
            key = st.value if hasattr(st, "value") else str(st).lower()
            if key in stats:
                stats[key] = count
            stats["total"] += count

        for r, count in role_rows:
            r_key = r.value if hasattr(r, "value") else str(r).lower()
            stats["by_role"][r_key] = count

        return stats

    async def get_admin_refund_stats(self) -> Dict[str, Any]:
        query = select(
            RefundRequest.status,
            func.count(RefundRequest.id).label("count"),
            func.coalesce(func.sum(RefundRequest.amount), 0).label("sum_amount"),
        ).group_by(RefundRequest.status)
        rows = (await self.db.execute(query)).all()

        stats = {
            "total_requests": 0,
            "pending": 0,
            "approved": 0,
            "processed": 0,
            "rejected": 0,
            "total_amount_refunded": 0.0,
        }

        for st, count, sum_amt in rows:
            key = st.value if hasattr(st, "value") else str(st).lower()
            if key in stats:
                stats[key] = count
            stats["total_requests"] += count
            if key in ["approved", "processed"]:
                stats["total_amount_refunded"] += float(sum_amt or 0.0)

        return stats


    async def get_admin_occupancy_today(self) -> Dict[str, int]:
        today = datetime.now(timezone.utc).date()

        in_query = select(func.count(Booking.id)).where(
            and_(
                Booking.check_in_date == today,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
            )
        )
        today_check_ins = (await self.db.execute(in_query)).scalar_one()

        out_query = select(func.count(Booking.id)).where(
            and_(
                Booking.check_out_date == today,
                Booking.status.in_([BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT]),
            )
        )
        today_check_outs = (await self.db.execute(out_query)).scalar_one()

        active_query = select(
            func.coalesce(func.sum(Booking.num_guests), 0)
        ).where(
            or_(
                Booking.status == BookingStatus.CHECKED_IN,
                and_(
                    Booking.check_in_date <= today,
                    Booking.check_out_date > today,
                    Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
                ),
            )
        )
        active_guests = (await self.db.execute(active_query)).scalar_one()

        return {
            "today_check_ins": int(today_check_ins or 0),
            "today_check_outs": int(today_check_outs or 0),
            "active_guests": int(active_guests or 0),
        }

    async def get_admin_revenue_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        # Generate list of month keys for last N months (e.g., '2026-08', '2026-07', ...)
        month_keys = []
        cur_year, cur_month = now.year, now.month
        for _ in range(months):
            month_keys.append(f"{cur_year:04d}-{cur_month:02d}")
            cur_month -= 1
            if cur_month == 0:
                cur_month = 12
                cur_year -= 1
        month_keys.reverse()

        earliest_month = month_keys[0]
        start_date = datetime.strptime(f"{earliest_month}-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # 1. Booking queries grouped by year-month
        month_col = func.to_char(Booking.created_at, "YYYY-MM")
        booking_query = (
            select(
                month_col.label("month_label"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Booking.status.not_in([BookingStatus.CANCELLED, BookingStatus.NO_SHOW]),
                                Booking.total_amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("revenue"),
                func.count(Booking.id).label("bookings_count"),
            )
            .where(Booking.created_at >= start_date)
            .group_by(month_col)
        )
        booking_rows = (await self.db.execute(booking_query)).all()
        booking_map = {row.month_label: (float(row.revenue or 0.0), int(row.bookings_count or 0)) for row in booking_rows}

        # 2. Payment queries grouped by year-month
        pay_month_col = func.to_char(Payment.created_at, "YYYY-MM")
        pay_query = (
            select(
                pay_month_col.label("month_label"),
                func.coalesce(func.sum(Payment.amount), 0).label("pay_gross"),
                func.coalesce(func.sum(Payment.refunded_amount), 0).label("pay_refunded"),
            )
            .where(
                Payment.created_at >= start_date,
                Payment.status.in_([
                    TransactionStatus.SUCCESS,
                    TransactionStatus.PARTIALLY_REFUNDED,
                    TransactionStatus.REFUNDED,
                ]),
            )
            .group_by(pay_month_col)
        )
        pay_rows = (await self.db.execute(pay_query)).all()
        pay_map = {row.month_label: (float(row.pay_gross or 0.0), float(row.pay_refunded or 0.0)) for row in pay_rows}

        # 3. RefundRequest queries grouped by year-month
        refund_month_col = func.to_char(RefundRequest.created_at, "YYYY-MM")
        refund_query = (
            select(
                refund_month_col.label("month_label"),
                func.coalesce(func.sum(RefundRequest.amount), 0).label("refund_sum"),
            )
            .where(
                RefundRequest.created_at >= start_date,
                or_(
                    RefundRequest.status == RefundRequestStatus.PROCESSED,
                    RefundRequest.status == RefundRequestStatus.APPROVED,
                    func.lower(func.cast(RefundRequest.status, String)).in_(["approved", "processed"]),
                ),
            )
            .group_by(refund_month_col)
        )
        refund_rows = (await self.db.execute(refund_query)).all()
        refund_map = {row.month_label: float(row.refund_sum or 0.0) for row in refund_rows}

        trends = []
        for mk in month_keys:
            b_gross, count = booking_map.get(mk, (0.0, 0))
            p_gross, p_ref = pay_map.get(mk, (0.0, 0.0))
            r_ref = refund_map.get(mk, 0.0)

            gross = max(p_gross, b_gross)
            ref = max(r_ref, p_ref)
            net = max(0.0, gross - ref)
            trends.append({
                "month": mk,
                "revenue": net,
                "gross_revenue": gross,
                "refunded": ref,
                "bookings_count": count,
            })
        return trends




    async def get_admin_recent_bookings(self, limit: int = 5) -> List[Dict[str, Any]]:
        query = (
            select(Booking)
            .options(
                selectinload(Booking.guest),
                selectinload(Booking.property),
            )
            .order_by(Booking.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        bookings = result.scalars().all()

        items = []
        for b in bookings:
            items.append({
                "id": str(b.public_id),
                "booking_reference": b.booking_reference,
                "guest_name": b.guest.full_name if b.guest else None,
                "guest_email": b.guest.email if b.guest else None,
                "property_name": b.property.name if b.property else None,
                "property_slug": b.property.slug if b.property else None,
                "check_in_date": b.check_in_date,
                "check_out_date": b.check_out_date,
                "num_guests": b.num_guests,
                "num_rooms": b.num_rooms,
                "total_amount": float(b.total_amount or 0.0),
                "currency": b.currency or "INR",
                "status": b.status.value if hasattr(b.status, "value") else str(b.status),
                "payment_status": b.payment_status.value if hasattr(b.payment_status, "value") else str(b.payment_status),
                "created_at": b.created_at,
            })
        return items

    async def get_admin_recent_host_requests(self, limit: int = 5) -> List[Dict[str, Any]]:
        query = (
            select(HostRequest)
            .order_by(HostRequest.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        requests = result.scalars().all()

        items = []
        for r in requests:
            items.append({
                "id": str(r.public_id),
                "full_name": r.full_name,
                "email": r.email,
                "phone": r.phone,
                "property_name": r.property_name,
                "property_type": r.property_type,
                "city": r.city,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "created_at": r.created_at,
            })
        return items

    async def get_admin_recent_users(self, limit: int = 5) -> List[Dict[str, Any]]:
        query = select(User).order_by(User.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()

        items = []
        for u in users:
            items.append({
                "id": str(u.public_id),
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role.value if hasattr(u.role, "value") else str(u.role),
                "status": u.status.value if hasattr(u.status, "value") else str(u.status),
                "created_at": u.created_at,
            })
        return items

    async def get_admin_recent_refund_requests(self, limit: int = 5) -> List[Dict[str, Any]]:
        query = (
            select(RefundRequest)
            .options(
                selectinload(RefundRequest.booking).selectinload(Booking.guest),
                selectinload(RefundRequest.booking).selectinload(Booking.property),
                selectinload(RefundRequest.requester),
            )
            .order_by(RefundRequest.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        requests = result.scalars().all()

        items = []
        for r in requests:
            booking = r.booking
            guest = (booking.guest if booking else None) or r.requester
            prop = booking.property if booking else None

            items.append({
                "id": str(r.public_id),
                "booking_reference": booking.booking_reference if booking else None,
                "guest_name": guest.full_name if guest else None,
                "guest_email": guest.email if guest else None,
                "property_name": prop.name if prop else None,
                "amount": float(r.amount or 0.0),
                "reason": r.reason,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "razorpay_refund_id": r.razorpay_refund_id,
                "approved_at": r.approved_at,
                "created_at": r.created_at,
            })
        return items


    async def get_admin_top_properties(self, limit: int = 5) -> List[Dict[str, Any]]:
        # Aggregate bookings count & revenue per property
        booking_subq = (
            select(
                Booking.property_id,
                func.count(Booking.id).label("booking_count"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Booking.status.not_in([BookingStatus.CANCELLED, BookingStatus.NO_SHOW]),
                                Booking.total_amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("total_revenue"),
            )
            .group_by(Booking.property_id)
            .subquery()
        )

        # Rating subquery
        review_subq = (
            select(
                Review.property_id,
                func.coalesce(func.avg(Review.rating), 0.0).label("avg_rating"),
            )
            .where(Review.status == ReviewStatus.PUBLISHED)
            .group_by(Review.property_id)
            .subquery()
        )

        query = (
            select(
                Property,
                City.name.label("city_name"),
                func.coalesce(booking_subq.c.booking_count, 0).label("bookings_count"),
                func.coalesce(booking_subq.c.total_revenue, 0).label("revenue_sum"),
                func.coalesce(review_subq.c.avg_rating, 0.0).label("avg_rating"),
            )
            .outerjoin(City, Property.city_id == City.id)
            .outerjoin(booking_subq, Property.id == booking_subq.c.property_id)
            .outerjoin(review_subq, Property.id == review_subq.c.property_id)
            .options(selectinload(Property.property_assets))
            .order_by(booking_subq.c.booking_count.desc().nullslast(), Property.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for prop, city_name, b_count, rev_sum, avg_rat in rows:
            cover_img = None
            if prop.property_assets:
                # Find cover or first asset
                cover = next(
                    (a.file_url for a in prop.property_assets if getattr(a, "is_cover", False) or getattr(a, "use_for", None) == "cover"),
                    prop.property_assets[0].file_url if prop.property_assets else None,
                )
                cover_img = cover

            items.append({
                "id": str(prop.public_id),
                "name": prop.name,
                "slug": prop.slug,
                "city": city_name,
                "type": prop.type.value if hasattr(prop.type, "value") else (str(prop.type) if prop.type else None),
                "price_per_night": float(prop.price_per_night or 0.0),
                "image_url": cover_img,
                "total_bookings": int(b_count or 0),
                "total_revenue": float(rev_sum or 0.0),
                "average_rating": round(float(avg_rat or 0.0), 1),
            })
        return items

    async def get_admin_payout_stats(self) -> Dict[str, Any]:
        query = select(
            Payout.status,
            func.count(Payout.id).label("count"),
            func.coalesce(func.sum(Payout.amount), 0).label("sum_amount"),
        ).group_by(Payout.status)
        rows = (await self.db.execute(query)).all()

        stats = {
            "total_payouts": 0,
            "total_paid_amount": 0.0,
            "pending_payout_amount": 0.0,
            "processing_payout_amount": 0.0,
            "failed_payout_amount": 0.0,
            "pending_count": 0,
            "processing_count": 0,
            "paid_count": 0,
            "failed_count": 0,
            "last_payout_date": None,
            "last_payout_amount": 0.0,
            "currency": "INR",
        }

        for st, count, sum_amt in rows:
            st_key = st.value if hasattr(st, "value") else str(st).lower()
            stats["total_payouts"] += count
            amt = float(sum_amt or 0.0)

            if st_key == "paid":
                stats["paid_count"] += count
                stats["total_paid_amount"] += amt
            elif st_key == "pending":
                stats["pending_count"] += count
                stats["pending_payout_amount"] += amt
            elif st_key == "processing":
                stats["processing_count"] += count
                stats["processing_payout_amount"] += amt
            elif st_key in ["failed", "rejected", "reversed"]:
                stats["failed_count"] += count
                stats["failed_payout_amount"] += amt

        last_payout_query = (
            select(Payout.paid_at, Payout.amount)
            .where(Payout.status == PayoutStatus.PAID)
            .order_by(Payout.paid_at.desc().nullslast(), Payout.created_at.desc())
            .limit(1)
        )
        last_payout_row = (await self.db.execute(last_payout_query)).first()
        if last_payout_row:
            stats["last_payout_date"] = last_payout_row[0]
            stats["last_payout_amount"] = float(last_payout_row[1] or 0.0)

        return stats

    async def get_admin_recent_payouts(self, limit: int = 5) -> List[Dict[str, Any]]:
        query = (
            select(Payout)
            .options(selectinload(Payout.vendor))
            .order_by(Payout.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        payouts = result.scalars().all()

        items = []
        for p in payouts:
            items.append({
                "id": str(p.public_id),
                "vendor_name": p.vendor.full_name if p.vendor else None,
                "vendor_email": p.vendor.email if p.vendor else None,
                "amount": float(p.amount or 0.0),
                "gross_amount": float(p.gross_amount or 0.0) if p.gross_amount is not None else 0.0,
                "commission_amount": float(p.commission_amount or 0.0) if p.commission_amount is not None else 0.0,
                "currency": p.currency or "INR",
                "period_start": p.period_start,
                "period_end": p.period_end,
                "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                "mode": p.mode or "NEFT",
                "utr": p.utr,
                "notes": p.notes,
                "paid_at": p.paid_at,
                "created_at": p.created_at,
            })
        return items

    # ──────────────────────────────────────────────────────────────────────────
    # VENDOR REPOSITORY METHODS (Scoped to vendor_id)
    # ──────────────────────────────────────────────────────────────────────────

    async def get_vendor_booking_stats(self, vendor_id: int) -> Dict[str, int]:
        query = (
            select(
                Booking.status,
                func.count(Booking.id).label("count"),
            )
            .join(Property, Booking.property_id == Property.id)
            .where(Property.vendor_id == vendor_id)
            .group_by(Booking.status)
        )
        result = await self.db.execute(query)
        rows = result.all()

        stats = {
            "total": 0,
            "pending": 0,
            "confirmed": 0,
            "checked_in": 0,
            "checked_out": 0,
            "cancelled": 0,
            "completed": 0,
            "no_show": 0,
        }

        for status_val, count in rows:
            key = status_val.value if hasattr(status_val, "value") else str(status_val).lower()
            if key in stats:
                stats[key] = count
            stats["total"] += count

        return stats

    async def get_vendor_revenue_stats(self, vendor_id: int) -> Dict[str, Any]:
        revenue_statuses = [
            BookingStatus.CONFIRMED,
            BookingStatus.CHECKED_IN,
            BookingStatus.CHECKED_OUT,
            BookingStatus.COMPLETED,
        ]
        paid_payment_statuses = [
            PaymentStatus.PAID,
            PaymentStatus.PARTIALLY_PAID,
        ]
        # Gross revenue from valid bookings for vendor
        rev_query = (
            select(func.coalesce(func.sum(Booking.total_amount), 0))
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                or_(
                    Booking.status.in_(revenue_statuses),
                    Booking.payment_status.in_(paid_payment_statuses),
                ),
            )
        )
        booking_revenue = (await self.db.execute(rev_query)).scalar_one()

        # Gross revenue from payments for vendor
        pay_gross_query = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .join(Booking, Payment.booking_id == Booking.id)
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                Payment.status.in_([
                    TransactionStatus.SUCCESS,
                    TransactionStatus.PARTIALLY_REFUNDED,
                    TransactionStatus.REFUNDED,
                ]),
            )
        )
        pay_gross = (await self.db.execute(pay_gross_query)).scalar_one()

        gross_revenue = max(float(pay_gross or 0.0), float(booking_revenue or 0.0))

        pending_query = (
            select(func.coalesce(func.sum(Booking.total_amount), 0))
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                and_(
                    Booking.status == BookingStatus.PENDING,
                    Booking.payment_status == PaymentStatus.PENDING,
                ),
            )
        )
        pending_revenue = (await self.db.execute(pending_query)).scalar_one()

        # Refunded amount from RefundRequest for vendor properties
        refund_req_query = (
            select(func.coalesce(func.sum(RefundRequest.amount), 0))
            .join(Booking, RefundRequest.booking_id == Booking.id)
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                or_(
                    RefundRequest.status == RefundRequestStatus.PROCESSED,
                    RefundRequest.status == RefundRequestStatus.APPROVED,
                    func.lower(func.cast(RefundRequest.status, String)).in_(["approved", "processed"]),
                ),
            )
        )
        refund_req_amount = (await self.db.execute(refund_req_query)).scalar_one()

        # Refunded amount from Payment for vendor properties
        payment_refund_query = (
            select(func.coalesce(func.sum(Payment.refunded_amount), 0))
            .join(Booking, Payment.booking_id == Booking.id)
            .join(Property, Booking.property_id == Property.id)
            .where(Property.vendor_id == vendor_id)
        )
        payment_refund_amount = (await self.db.execute(payment_refund_query)).scalar_one()

        refunded_amount = max(float(refund_req_amount or 0.0), float(payment_refund_amount or 0.0))
        net_revenue = max(0.0, float(gross_revenue or 0.0) - float(refunded_amount or 0.0))

        return {
            "total_revenue": float(net_revenue or 0.0),
            "gross_revenue": float(gross_revenue or 0.0),
            "net_revenue": float(net_revenue or 0.0),
            "pending_revenue": float(pending_revenue or 0.0),
            "refunded_amount": float(refunded_amount or 0.0),
            "total_refunded": float(refunded_amount or 0.0),
            "currency": "INR",
        }




    async def get_vendor_property_stats(self, vendor_id: int) -> Dict[str, Any]:
        status_query = (
            select(
                Property.status,
                func.count(Property.id).label("count"),
            )
            .where(Property.vendor_id == vendor_id)
            .group_by(Property.status)
        )
        status_rows = (await self.db.execute(status_query)).all()

        featured_query = (
            select(func.count(Property.id))
            .where(
                Property.vendor_id == vendor_id,
                Property.is_featured.is_(True),
            )
        )
        featured_count = (await self.db.execute(featured_query)).scalar_one()

        stats = {
            "total": 0,
            "active": 0,
            "draft": 0,
            "inactive": 0,
            "archived": 0,
            "featured": int(featured_count or 0),
            "by_type": {},
        }

        for st, count in status_rows:
            key = st.value if hasattr(st, "value") else str(st).lower()
            if key in stats:
                stats[key] = count
            stats["total"] += count

        return stats

    async def get_vendor_review_stats(self, vendor_id: int) -> Dict[str, Any]:
        query = (
            select(
                func.count(Review.id).label("total_reviews"),
                func.coalesce(func.avg(Review.rating), 0.0).label("avg_rating"),
            )
            .join(Property, Review.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                Review.status == ReviewStatus.PUBLISHED,
            )
        )
        result = await self.db.execute(query)
        row = result.one()

        return {
            "total_reviews": int(row.total_reviews or 0),
            "average_rating": round(float(row.avg_rating or 0.0), 1),
        }

    async def get_vendor_occupancy_today(self, vendor_id: int) -> Dict[str, int]:
        today = datetime.now(timezone.utc).date()

        in_query = (
            select(func.count(Booking.id))
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                Booking.check_in_date == today,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
            )
        )
        today_check_ins = (await self.db.execute(in_query)).scalar_one()

        out_query = (
            select(func.count(Booking.id))
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                Booking.check_out_date == today,
                Booking.status.in_([BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT]),
            )
        )
        today_check_outs = (await self.db.execute(out_query)).scalar_one()

        active_query = (
            select(func.coalesce(func.sum(Booking.num_guests), 0))
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                or_(
                    Booking.status == BookingStatus.CHECKED_IN,
                    and_(
                        Booking.check_in_date <= today,
                        Booking.check_out_date > today,
                        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
                    ),
                ),
            )
        )
        active_guests = (await self.db.execute(active_query)).scalar_one()

        return {
            "today_check_ins": int(today_check_ins or 0),
            "today_check_outs": int(today_check_outs or 0),
            "active_guests": int(active_guests or 0),
        }

    async def get_vendor_revenue_trends(self, vendor_id: int, months: int = 12) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        month_keys = []
        cur_year, cur_month = now.year, now.month
        for _ in range(months):
            month_keys.append(f"{cur_year:04d}-{cur_month:02d}")
            cur_month -= 1
            if cur_month == 0:
                cur_month = 12
                cur_year -= 1
        month_keys.reverse()

        earliest_month = month_keys[0]
        start_date = datetime.strptime(f"{earliest_month}-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # 1. Booking queries grouped by year-month for vendor
        month_col = func.to_char(Booking.created_at, "YYYY-MM")
        booking_query = (
            select(
                month_col.label("month_label"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Booking.status.not_in([BookingStatus.CANCELLED, BookingStatus.NO_SHOW]),
                                Booking.total_amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("revenue"),
                func.count(Booking.id).label("bookings_count"),
            )
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                Booking.created_at >= start_date,
            )
            .group_by(month_col)
        )
        booking_rows = (await self.db.execute(booking_query)).all()
        booking_map = {row.month_label: (float(row.revenue or 0.0), int(row.bookings_count or 0)) for row in booking_rows}

        # 2. Payment queries grouped by year-month for vendor
        pay_month_col = func.to_char(Payment.created_at, "YYYY-MM")
        pay_query = (
            select(
                pay_month_col.label("month_label"),
                func.coalesce(func.sum(Payment.amount), 0).label("pay_gross"),
                func.coalesce(func.sum(Payment.refunded_amount), 0).label("pay_refunded"),
            )
            .join(Booking, Payment.booking_id == Booking.id)
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                Payment.created_at >= start_date,
                Payment.status.in_([
                    TransactionStatus.SUCCESS,
                    TransactionStatus.PARTIALLY_REFUNDED,
                    TransactionStatus.REFUNDED,
                ]),
            )
            .group_by(pay_month_col)
        )
        pay_rows = (await self.db.execute(pay_query)).all()
        pay_map = {row.month_label: (float(row.pay_gross or 0.0), float(row.pay_refunded or 0.0)) for row in pay_rows}

        # 3. Query refunds grouped by year-month for vendor
        refund_month_col = func.to_char(RefundRequest.created_at, "YYYY-MM")
        refund_query = (
            select(
                refund_month_col.label("month_label"),
                func.coalesce(func.sum(RefundRequest.amount), 0).label("refund_sum"),
            )
            .join(Booking, RefundRequest.booking_id == Booking.id)
            .join(Property, Booking.property_id == Property.id)
            .where(
                Property.vendor_id == vendor_id,
                RefundRequest.created_at >= start_date,
                or_(
                    RefundRequest.status == RefundRequestStatus.PROCESSED,
                    RefundRequest.status == RefundRequestStatus.APPROVED,
                    func.lower(func.cast(RefundRequest.status, String)).in_(["approved", "processed"]),
                ),
            )
            .group_by(refund_month_col)
        )
        refund_rows = (await self.db.execute(refund_query)).all()
        refund_map = {row.month_label: float(row.refund_sum or 0.0) for row in refund_rows}

        trends = []
        for mk in month_keys:
            b_gross, count = booking_map.get(mk, (0.0, 0))
            p_gross, p_ref = pay_map.get(mk, (0.0, 0.0))
            r_ref = refund_map.get(mk, 0.0)

            gross = max(p_gross, b_gross)
            ref = max(r_ref, p_ref)
            net = max(0.0, gross - ref)
            trends.append({
                "month": mk,
                "revenue": net,
                "gross_revenue": gross,
                "refunded": ref,
                "bookings_count": count,
            })
        return trends




    async def get_vendor_recent_bookings(self, vendor_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        query = (
            select(Booking)
            .join(Property, Booking.property_id == Property.id)
            .options(
                selectinload(Booking.guest),
                selectinload(Booking.property),
            )
            .where(Property.vendor_id == vendor_id)
            .order_by(Booking.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        bookings = result.scalars().all()

        items = []
        for b in bookings:
            items.append({
                "id": str(b.public_id),
                "booking_reference": b.booking_reference,
                "guest_name": b.guest.full_name if b.guest else None,
                "guest_email": b.guest.email if b.guest else None,
                "property_name": b.property.name if b.property else None,
                "property_slug": b.property.slug if b.property else None,
                "check_in_date": b.check_in_date,
                "check_out_date": b.check_out_date,
                "num_guests": b.num_guests,
                "num_rooms": b.num_rooms,
                "total_amount": float(b.total_amount or 0.0),
                "currency": b.currency or "INR",
                "status": b.status.value if hasattr(b.status, "value") else str(b.status),
                "payment_status": b.payment_status.value if hasattr(b.payment_status, "value") else str(b.payment_status),
                "created_at": b.created_at,
            })
        return items

    async def get_vendor_upcoming_bookings(self, vendor_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        today = datetime.now(timezone.utc).date()
        query = (
            select(Booking)
            .join(Property, Booking.property_id == Property.id)
            .options(
                selectinload(Booking.guest),
                selectinload(Booking.property),
            )
            .where(
                Property.vendor_id == vendor_id,
                Booking.check_in_date >= today,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            )
            .order_by(Booking.check_in_date.asc(), Booking.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        bookings = result.scalars().all()

        items = []
        for b in bookings:
            items.append({
                "id": str(b.public_id),
                "booking_reference": b.booking_reference,
                "guest_name": b.guest.full_name if b.guest else None,
                "guest_email": b.guest.email if b.guest else None,
                "property_name": b.property.name if b.property else None,
                "property_slug": b.property.slug if b.property else None,
                "check_in_date": b.check_in_date,
                "check_out_date": b.check_out_date,
                "num_guests": b.num_guests,
                "num_rooms": b.num_rooms,
                "total_amount": float(b.total_amount or 0.0),
                "currency": b.currency or "INR",
                "status": b.status.value if hasattr(b.status, "value") else str(b.status),
                "payment_status": b.payment_status.value if hasattr(b.payment_status, "value") else str(b.payment_status),
                "created_at": b.created_at,
            })
        return items

    async def get_vendor_top_properties(self, vendor_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        booking_subq = (
            select(
                Booking.property_id,
                func.count(Booking.id).label("booking_count"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Booking.status.not_in([BookingStatus.CANCELLED, BookingStatus.NO_SHOW]),
                                Booking.total_amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("total_revenue"),
            )
            .group_by(Booking.property_id)
            .subquery()
        )

        review_subq = (
            select(
                Review.property_id,
                func.coalesce(func.avg(Review.rating), 0.0).label("avg_rating"),
            )
            .where(Review.status == ReviewStatus.PUBLISHED)
            .group_by(Review.property_id)
            .subquery()
        )

        query = (
            select(
                Property,
                City.name.label("city_name"),
                func.coalesce(booking_subq.c.booking_count, 0).label("bookings_count"),
                func.coalesce(booking_subq.c.total_revenue, 0).label("revenue_sum"),
                func.coalesce(review_subq.c.avg_rating, 0.0).label("avg_rating"),
            )
            .outerjoin(City, Property.city_id == City.id)
            .outerjoin(booking_subq, Property.id == booking_subq.c.property_id)
            .outerjoin(review_subq, Property.id == review_subq.c.property_id)
            .options(selectinload(Property.property_assets))
            .where(Property.vendor_id == vendor_id)
            .order_by(booking_subq.c.booking_count.desc().nullslast(), Property.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for prop, city_name, b_count, rev_sum, avg_rat in rows:
            cover_img = None
            if prop.property_assets:
                cover = next(
                    (a.file_url for a in prop.property_assets if getattr(a, "is_cover", False) or getattr(a, "use_for", None) == "cover"),
                    prop.property_assets[0].file_url if prop.property_assets else None,
                )
                cover_img = cover

            items.append({
                "id": str(prop.public_id),
                "name": prop.name,
                "slug": prop.slug,
                "city": city_name,
                "type": prop.type.value if hasattr(prop.type, "value") else (str(prop.type) if prop.type else None),
                "price_per_night": float(prop.price_per_night or 0.0),
                "image_url": cover_img,
                "total_bookings": int(b_count or 0),
                "total_revenue": float(rev_sum or 0.0),
                "average_rating": round(float(avg_rat or 0.0), 1),
            })
        return items

    async def get_vendor_payout_stats(self, vendor_id: int) -> Dict[str, Any]:
        query = (
            select(
                Payout.status,
                func.count(Payout.id).label("count"),
                func.coalesce(func.sum(Payout.amount), 0).label("sum_amount"),
            )
            .where(Payout.vendor_id == vendor_id)
            .group_by(Payout.status)
        )
        rows = (await self.db.execute(query)).all()

        stats = {
            "total_payouts": 0,
            "total_paid_amount": 0.0,
            "pending_payout_amount": 0.0,
            "processing_payout_amount": 0.0,
            "failed_payout_amount": 0.0,
            "pending_count": 0,
            "processing_count": 0,
            "paid_count": 0,
            "failed_count": 0,
            "last_payout_date": None,
            "last_payout_amount": 0.0,
            "currency": "INR",
        }

        for st, count, sum_amt in rows:
            st_key = st.value if hasattr(st, "value") else str(st).lower()
            stats["total_payouts"] += count
            amt = float(sum_amt or 0.0)

            if st_key == "paid":
                stats["paid_count"] += count
                stats["total_paid_amount"] += amt
            elif st_key == "pending":
                stats["pending_count"] += count
                stats["pending_payout_amount"] += amt
            elif st_key == "processing":
                stats["processing_count"] += count
                stats["processing_payout_amount"] += amt
            elif st_key in ["failed", "rejected", "reversed"]:
                stats["failed_count"] += count
                stats["failed_payout_amount"] += amt

        last_payout_query = (
            select(Payout.paid_at, Payout.amount)
            .where(
                Payout.vendor_id == vendor_id,
                Payout.status == PayoutStatus.PAID,
            )
            .order_by(Payout.paid_at.desc().nullslast(), Payout.created_at.desc())
            .limit(1)
        )
        last_payout_row = (await self.db.execute(last_payout_query)).first()
        if last_payout_row:
            stats["last_payout_date"] = last_payout_row[0]
            stats["last_payout_amount"] = float(last_payout_row[1] or 0.0)

        return stats

    async def get_vendor_recent_payouts(self, vendor_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        query = (
            select(Payout)
            .options(selectinload(Payout.vendor))
            .where(Payout.vendor_id == vendor_id)
            .order_by(Payout.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        payouts = result.scalars().all()

        items = []
        for p in payouts:
            items.append({
                "id": str(p.public_id),
                "vendor_name": p.vendor.full_name if p.vendor else None,
                "vendor_email": p.vendor.email if p.vendor else None,
                "amount": float(p.amount or 0.0),
                "gross_amount": float(p.gross_amount or 0.0) if p.gross_amount is not None else 0.0,
                "commission_amount": float(p.commission_amount or 0.0) if p.commission_amount is not None else 0.0,
                "currency": p.currency or "INR",
                "period_start": p.period_start,
                "period_end": p.period_end,
                "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                "mode": p.mode or "NEFT",
                "utr": p.utr,
                "notes": p.notes,
                "paid_at": p.paid_at,
                "created_at": p.created_at,
            })
        return items

