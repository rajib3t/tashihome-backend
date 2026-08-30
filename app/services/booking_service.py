from datetime import date, datetime, time, timezone
import secrets
from typing import Any, Dict, Optional, Tuple

from app.core.exceptions import AppException
from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.cancellation_policy_model import CancellationPolicy
from app.models.property_model import Property
from app.models.property_room_type_model import PropertyRoomType
from app.models.refund_request_model import RefundRequest, RefundRequestStatus
from app.repositories.base_repository import Page
from app.repositories.booking_repository import BookingRepository, BookingWithRelations
from app.repositories.cancellation_policy_repository import CancellationPolicyRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.property_room_type_repository import PropertyRoomTypeRepository
from app.repositories.refund_request_repository import RefundRequestRepository
from app.repositories.room_block_repository import RoomBlockRepository


class BookingService:
    def __init__(
        self,
        booking_repository: BookingRepository,
        property_repository: PropertyRepository,
        property_room_type_repository: PropertyRoomTypeRepository,
        room_block_repository: RoomBlockRepository,
        refund_request_repository: RefundRequestRepository,
    ):
        self.booking_repository = booking_repository
        self.property_repository = property_repository
        self.property_room_type_repository = property_room_type_repository
        self.room_block_repository = room_block_repository
        self.refund_request_repository = refund_request_repository

    @staticmethod
    def generate_booking_reference() -> str:
        """Generates a readable, unique booking reference string like BK20260830AB12."""
        today_str = datetime.now(timezone.utc).strftime("%y%m%d")
        rand_token = secrets.token_hex(3).upper()
        return f"BK{today_str}{rand_token}"

    async def generate_invoice_number(self) -> str:
        """
        Generate the next unique sequential invoice number for the current month.
        Format: INV-YYYYMM-NNNNNNN (e.g., INV-202608-0000001).
        Delegates to repository which uses SELECT FOR UPDATE for atomicity.
        """
        return await self.booking_repository.get_next_invoice_number()

    async def get_total_units(self, property_id: int, room_type_id: Optional[int]) -> int:
        """Determines the configured total units for a room type or property."""
        if room_type_id is not None:
            prop_room_type = await self.property_room_type_repository.get_by_property_and_room_type(
                property_id, room_type_id
            )
            if prop_room_type and prop_room_type.total_units:
                return prop_room_type.total_units
        return 1

    async def check_availability(
        self,
        property_id: int,
        room_type_id: Optional[int],
        check_in_date: date,
        check_out_date: date,
        num_rooms: int = 1,
        exclude_booking_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculates availability for a property / room type over a date range.
        """
        total_units = await self.get_total_units(property_id, room_type_id)
        booked_units = await self.booking_repository.count_booked_units(
            property_id=property_id,
            room_type_id=room_type_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            exclude_booking_id=exclude_booking_id,
        )
        blocked_units = await self.room_block_repository.count_blocked_units(
            property_id=property_id,
            room_type_id=room_type_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
        )

        available_units = max(0, total_units - (booked_units + blocked_units))
        is_available = available_units >= num_rooms

        return {
            "is_available": is_available,
            "total_units": total_units,
            "booked_units": booked_units,
            "blocked_units": blocked_units,
            "available_units": available_units,
            "requested_rooms": num_rooms,
        }

    def calculate_pricing_quote(
        self,
        property_: Property,
        check_in_date: date,
        check_out_date: date,
        num_rooms: int = 1,
        num_guests: int = 1,
    ) -> Dict[str, Any]:
        """
        Calculates nights, nightly rate, taxes, discount, and total price.
        """
        nights = (check_out_date - check_in_date).days
        if nights < 1:
            raise AppException(
                status_code=400,
                message="Check-out date must be after check-in date.",
                error_code="INVALID_DATES",
                field="check_out_date",
            )

        # Price per night: check sale_per_night first if positive, else price_per_night
        price_per_night = float(
            property_.sale_per_night
            if property_.sale_per_night and property_.sale_per_night > 0
            else (property_.price_per_night or 0)
        )

        base_amount = price_per_night * num_rooms * nights
        discount_amount = 0.0
        tax_amount = 0.0
        total_amount = round(base_amount - discount_amount + tax_amount, 2)
        currency = property_.currency or "INR"

        return {
            "nights": nights,
            "num_rooms": num_rooms,
            "num_guests": num_guests,
            "price_per_night": price_per_night,
            "base_amount": round(base_amount, 2),
            "discount_amount": round(discount_amount, 2),
            "tax_amount": round(tax_amount, 2),
            "total_amount": total_amount,
            "currency": currency,
        }

    def calculate_cancellation_refund(
        self,
        booking: Booking,
        total_paid: float,
    ) -> Tuple[float, float, str]:
        """
        Calculates refund percentage and refundable amount based on cancellation policy.
        Returns: (refund_percentage, refund_amount, policy_summary)
        """
        if total_paid <= 0:
            return 0.0, 0.0, "No payment made"

        now = datetime.now(timezone.utc)
        check_in_dt = datetime.combine(booking.check_in_date, time(14, 0), tzinfo=timezone.utc)
        hours_until_check_in = (check_in_dt - now).total_seconds() / 3600.0

        policy = booking.cancellation_policy
        if policy and policy.refund_tiers and isinstance(policy.refund_tiers, list):
            # Sort tiers descending by hours_before
            sorted_tiers = sorted(
                policy.refund_tiers,
                key=lambda x: float(x.get("hours_before", 0)),
                reverse=True,
            )
            for tier in sorted_tiers:
                hours_before = float(tier.get("hours_before", 0))
                refund_pct = float(tier.get("refund_percent", 0))
                if hours_until_check_in >= hours_before:
                    refund_amount = round(total_paid * (refund_pct / 100.0), 2)
                    return refund_pct, refund_amount, f"{refund_pct}% refund if cancelled >= {hours_before}h before check-in"

            return 0.0, 0.0, "Non-refundable at this time"

        # Default fallback policy if no tiers defined
        if hours_until_check_in >= 48:
            return 100.0, round(total_paid, 2), "100% refund (cancelled >= 48h before check-in)"
        elif hours_until_check_in >= 24:
            return 50.0, round(total_paid * 0.5, 2), "50% refund (cancelled >= 24h before check-in)"
        else:
            return 0.0, 0.0, "Non-refundable (< 24h before check-in)"

    async def create_booking(
        self,
        booking: Booking,
        with_relations: Optional[BookingWithRelations] = None,
        commit: bool = True,
    ) -> Booking:
        return await self.booking_repository.create(
            booking=booking,
            with_relations=with_relations,
            commit=commit,
        )

    async def get_by_id(
        self,
        booking_id: int,
        with_relations: Optional[BookingWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Booking]:
        return await self.booking_repository.get_by_id(
            booking_id=booking_id,
            with_relations=with_relations,
            flush=flush,
        )

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[BookingWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Booking]:
        return await self.booking_repository.get_by_public_id(
            public_id=public_id,
            with_relations=with_relations,
            flush=flush,
        )

    async def get_user_booking_by_identifier(
        self,
        guest_id: int,
        identifier: str,
        with_relations: Optional[BookingWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Booking]:
        return await self.booking_repository.get_user_booking_by_identifier(
            guest_id=guest_id,
            identifier=identifier,
            with_relations=with_relations,
            flush=flush,
        )

    async def update_booking(
        self,
        booking: Booking,
        with_relations: Optional[BookingWithRelations] = None,
        commit: bool = True,
    ) -> Booking:
        return await self.booking_repository.update(
            booking=booking,
            with_relations=with_relations,
            commit=commit,
        )

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
        return await self.booking_repository.list_user_bookings(
            guest_id=guest_id,
            page=page,
            page_size=page_size,
            status=status,
            payment_status=payment_status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            with_relations=with_relations,
            flush=flush,
        )

    async def get_booking_by_identifier(
        self,
        identifier: str,
        with_relations=None,
        flush: bool = False,
    ):
        """Fetch a booking by public_id or booking_reference — no guest restriction (admin/vendor)."""
        return await self.booking_repository.get_by_identifier(
            identifier=identifier,
            with_relations=with_relations,
            flush=flush,
        )

    async def list_all_bookings(
        self,
        page: int = 1,
        page_size: int = 10,
        status=None,
        payment_status=None,
        property_id=None,
        guest_id=None,
        check_in_from=None,
        check_in_to=None,
        search=None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        with_relations=None,
        flush: bool = False,
    ):
        """List all bookings (admin)."""
        return await self.booking_repository.list_all_bookings(
            page=page,
            page_size=page_size,
            status=status,
            payment_status=payment_status,
            property_id=property_id,
            guest_id=guest_id,
            check_in_from=check_in_from,
            check_in_to=check_in_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            with_relations=with_relations,
            flush=flush,
        )

    async def list_vendor_bookings(
        self,
        vendor_id: int,
        page: int = 1,
        page_size: int = 10,
        status=None,
        payment_status=None,
        property_id=None,
        check_in_from=None,
        check_in_to=None,
        search=None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        with_relations=None,
        flush: bool = False,
    ):
        """List bookings scoped to vendor's properties."""
        return await self.booking_repository.list_vendor_bookings(
            vendor_id=vendor_id,
            page=page,
            page_size=page_size,
            status=status,
            payment_status=payment_status,
            property_id=property_id,
            check_in_from=check_in_from,
            check_in_to=check_in_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            with_relations=with_relations,
            flush=flush,
        )
