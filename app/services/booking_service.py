from datetime import date, datetime, time, timezone
import math
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
        else:
            prop_room_types = await self.property_room_type_repository.get_by_property_id(property_id)
            if prop_room_types:
                total = sum(prt.total_units for prt in prop_room_types if prt.total_units)
                return total if total > 0 else 1
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

        # Build per-room-type availability breakdown
        room_types_availability = []
        prop_room_types = await self.property_room_type_repository.get_by_property_id(
            property_id, with_relations={"room_type": True, "pricing_tiers": True}
        )
        if prop_room_types:
            for prt in prop_room_types:
                prt_total = prt.total_units or 1
                prt_booked = await self.booking_repository.count_booked_units(
                    property_id=property_id,
                    room_type_id=prt.room_type_id,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    exclude_booking_id=exclude_booking_id,
                )
                prt_blocked = await self.room_block_repository.count_blocked_units(
                    property_id=property_id,
                    room_type_id=prt.room_type_id,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                )
                prt_available = max(0, prt_total - (prt_booked + prt_blocked))

                pricing_tiers_data = [
                    {
                        "id": str(tier.public_id),
                        "occupancy": tier.occupancy,
                        "price_per_night": float(tier.price_per_night),
                        "sale_per_night": float(tier.sale_per_night or 0),
                    }
                    for tier in (getattr(prt, "pricing_tiers", None) or [])
                ]

                room_types_availability.append({
                    "property_room_type_id": str(prt.public_id),
                    "room_type_id": str(prt.room_type.public_id) if prt.room_type else None,
                    "room_type_name": prt.room_type.name if prt.room_type else None,
                    "capacity": prt.room_type.capacity if prt.room_type else None,
                    "price_per_night": float(prt.price_per_night) if prt.price_per_night is not None else None,
                    "sale_per_night": float(prt.sale_per_night) if prt.sale_per_night is not None else None,
                    "pricing_tiers": pricing_tiers_data,
                    "total_units": prt_total,
                    "booked_units": prt_booked,
                    "blocked_units": prt_blocked,
                    "available_units": prt_available,
                    "is_available": prt_available >= num_rooms,
                })

        return {
            "is_available": is_available,
            "total_units": total_units,
            "booked_units": booked_units,
            "blocked_units": blocked_units,
            "available_units": available_units,
            "requested_rooms": num_rooms,
            "room_types_availability": room_types_availability,
        }

    def calculate_pricing_quote(
        self,
        property_: Property,
        check_in_date: date,
        check_out_date: date,
        num_rooms: int = 1,
        num_guests: int = 1,
        room_type_id: Optional[int] = None,
        property_room_type: Optional[PropertyRoomType] = None,
        tax_rate: float = 0.0,
        is_tax_inclusive: bool = False,
        tax_name: Optional[str] = None,
        tax_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates nights, nightly rate (factoring in room capacity & occupancy tiers),
        taxes, discount, and total price.
        """
        nights = (check_out_date - check_in_date).days
        if nights < 1:
            raise AppException(
                status_code=400,
                message="Check-out date must be after check-in date.",
                error_code="INVALID_DATES",
                field="check_out_date",
            )

        num_rooms = max(1, num_rooms)
        num_guests = max(1, num_guests)
        guests_per_room = max(1, math.ceil(num_guests / num_rooms))

        # 1. Resolve Target PropertyRoomType
        target_prt: Optional[PropertyRoomType] = property_room_type
        if not target_prt and property_ and getattr(property_, "property_room_types", None):
            if room_type_id is not None:
                for prt in property_.property_room_types:
                    if prt.room_type_id == room_type_id or getattr(prt, "id", None) == room_type_id:
                        target_prt = prt
                        break
            elif len(property_.property_room_types) == 1:
                target_prt = property_.property_room_types[0]

        # 2. Determine price_per_night based on room occupancy pricing_tiers
        price_per_night: float = 0.0
        applied_tier: Optional[Dict[str, Any]] = None

        if target_prt and getattr(target_prt, "pricing_tiers", None):
            tiers = list(target_prt.pricing_tiers)
            sorted_tiers = sorted(tiers, key=lambda t: t.occupancy)

            # Check exact match
            matched_tier = next((t for t in sorted_tiers if t.occupancy == guests_per_room), None)
            if not matched_tier:
                # If no exact match: pick closest tier (highest <= guests_per_room, or lowest >= guests_per_room)
                lower_tiers = [t for t in sorted_tiers if t.occupancy <= guests_per_room]
                if lower_tiers:
                    matched_tier = lower_tiers[-1]
                elif sorted_tiers:
                    matched_tier = sorted_tiers[0]

            if matched_tier:
                tier_sale = float(matched_tier.sale_per_night) if matched_tier.sale_per_night is not None else 0.0
                tier_price = float(matched_tier.price_per_night) if matched_tier.price_per_night is not None else 0.0
                price_per_night = tier_sale if tier_sale > 0 and (tier_price == 0 or tier_sale < tier_price) else tier_price
                applied_tier = {
                    "occupancy": matched_tier.occupancy,
                    "price_per_night": tier_price,
                    "sale_per_night": tier_sale,
                }

        # Fallback to room type base price
        if price_per_night <= 0 and target_prt:
            prt_sale = float(target_prt.sale_per_night) if target_prt.sale_per_night is not None else 0.0
            prt_price = float(target_prt.price_per_night) if target_prt.price_per_night is not None else 0.0
            if prt_sale > 0 and (prt_price == 0 or prt_sale < prt_price):
                price_per_night = prt_sale
            elif prt_price > 0:
                price_per_night = prt_price

        # Fallback to property level price
        if price_per_night <= 0 and property_:
            prop_sale = float(property_.sale_per_night) if property_.sale_per_night is not None else 0.0
            prop_price = float(property_.price_per_night) if property_.price_per_night is not None else 0.0
            if prop_sale > 0 and (prop_price == 0 or prop_sale < prop_price):
                price_per_night = prop_sale
            else:
                price_per_night = prop_price

        base_amount = round(price_per_night * num_rooms * nights, 2)
        discount_amount = 0.0
        tax_amount = 0.0

        if tax_rate > 0:
            if is_tax_inclusive:
                net_base = base_amount / (1 + (tax_rate / 100.0))
                tax_amount = round(base_amount - net_base, 2)
                total_amount = round(base_amount - discount_amount, 2)
            else:
                tax_amount = round((base_amount - discount_amount) * (tax_rate / 100.0), 2)
                total_amount = round(base_amount - discount_amount + tax_amount, 2)
        else:
            total_amount = round(base_amount - discount_amount, 2)

        currency = property_.currency if (property_ and property_.currency) else "INR"

        return {
            "nights": nights,
            "num_rooms": num_rooms,
            "num_guests": num_guests,
            "guests_per_room": guests_per_room,
            "price_per_night": price_per_night,
            "base_amount": base_amount,
            "discount_amount": round(discount_amount, 2),
            "tax_amount": tax_amount,
            "tax_rate": tax_rate,
            "is_tax_inclusive": is_tax_inclusive,
            "tax_name": tax_name,
            "tax_code": tax_code,
            "total_amount": total_amount,
            "currency": currency,
            "applied_tier": applied_tier,
            "room_type_id": str(target_prt.room_type.public_id) if target_prt and getattr(target_prt, "room_type", None) else None,
            "room_type_name": target_prt.room_type.name if target_prt and getattr(target_prt, "room_type", None) else None,
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
