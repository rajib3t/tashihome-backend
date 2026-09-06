from datetime import date
from typing import Optional, Tuple
from uuid import UUID

from app.application.dto.bookings.booking import BookingCreateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.config import settings
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.property_model import PropertyStatus
from app.services.booking_service import BookingService
from app.services.property_room_type_service import PropertyRoomTypeService
from app.services.property_service import PropertyService
from app.services.room_type_service import RoomTypeService
from app.services.setting_service import SettingService
from app.services.tax_service import TaxService


class CreateBookingUseCase(BaseUseCase):
    def __init__(
        self,
        booking_service: BookingService,
        property_service: PropertyService,
        room_type_service: RoomTypeService,
        current_user: CurrentUser,
        property_room_type_service: Optional[PropertyRoomTypeService] = None,
        tax_service: Optional[TaxService] = None,
        setting_service: Optional[SettingService] = None,
    ):
        self.booking_service = booking_service
        self.property_service = property_service
        self.room_type_service = room_type_service
        self.current_user = current_user
        self.property_room_type_service = property_room_type_service
        self.tax_service = tax_service
        self.setting_service = setting_service

    async def _resolve_tax_settings(self) -> Tuple[float, bool, Optional[str], Optional[str]]:
        """Resolve default active tax settings for pricing calculation."""
        if self.tax_service:
            try:
                default_tax = await self.tax_service.get_default_tax()
                if default_tax and default_tax.rate is not None:
                    return (
                        float(default_tax.rate),
                        bool(default_tax.is_inclusive),
                        default_tax.name,
                        default_tax.code,
                    )
            except Exception:
                pass

        if self.setting_service:
            try:
                is_gst_enabled = await self.setting_service.get_value("is_gst_enabled", "false")
                if is_gst_enabled and is_gst_enabled.lower() == "true":
                    gst_pct = await self.setting_service.get_value("gst_percentage", "0")
                    is_inc = await self.setting_service.get_value("is_tax_inclusive", "false")
                    rate = float(gst_pct or 0)
                    return rate, is_inc.lower() == "true", "GST", "GST"
            except Exception:
                pass

        return 0.0, False, None, None

    async def execute(self, data: BookingCreateDTO) -> Booking:
        if not settings.PAYMENT_ENABLED:
            raise AppException(
                status_code=400,
                message="Payment processing is currently disabled.",
                error_code="PAYMENT_DISABLED",
            )
        today = date.today()
        if data.check_in_date < today:
            raise AppException(
                status_code=400,
                message="Check-in date cannot be in the past.",
                error_code="INVALID_CHECK_IN_DATE",
                field="check_in_date",
            )

        if data.check_out_date <= data.check_in_date:
            raise AppException(
                status_code=400,
                message="Check-out date must be after check-in date.",
                error_code="INVALID_CHECK_OUT_DATE",
                field="check_out_date",
            )

        # 1. Resolve Property
        property_ = None
        try:
            uuid_obj = UUID(str(data.property_id))
            property_ = await self.property_service.get_by_public_id(
                str(uuid_obj),
                with_relations={"cancellation_policy": True, "property_room_types": True},
            )
        except (ValueError, AttributeError):
            if str(data.property_id).isdigit():
                property_ = await self.property_service.get_by_id(
                    int(data.property_id),
                    with_relations={"cancellation_policy": True, "property_room_types": True},
                )
            else:
                property_ = await self.property_service.get_by_slug(
                    str(data.property_id),
                    with_relations={"cancellation_policy": True, "property_room_types": True},
                )

        if not property_:
            raise AppException(
                status_code=404,
                message="Property not found.",
                error_code="PROPERTY_NOT_FOUND",
                field="property_id",
            )

        if property_.status != PropertyStatus.ACTIVE:
            raise AppException(
                status_code=400,
                message="Property is currently not active for bookings.",
                error_code="PROPERTY_NOT_ACTIVE",
            )

        # 2. Resolve Room Type if provided
        room_type_id_db: Optional[int] = None
        if data.room_type_id:
            room_type = None
            try:
                rt_uuid = UUID(str(data.room_type_id))
                room_type = await self.room_type_service.get_by_public_id(str(rt_uuid))
                if not room_type and hasattr(self, "property_room_type_service") and self.property_room_type_service:
                    prop_rt = await self.property_room_type_service.get_by_public_id(str(rt_uuid))
                    if prop_rt:
                        room_type_id_db = prop_rt.room_type_id
            except (ValueError, AttributeError):
                if str(data.room_type_id).isdigit():
                    room_type = await self.room_type_service.get_by_id(int(data.room_type_id))
                    if not room_type and hasattr(self, "property_room_type_service") and self.property_room_type_service:
                        prop_rt = await self.property_room_type_service.get_by_id(int(data.room_type_id))
                        if prop_rt:
                            room_type_id_db = prop_rt.room_type_id

            if room_type:
                room_type_id_db = room_type.id
            elif room_type_id_db is None:
                raise AppException(
                    status_code=404,
                    message="Room type not found.",
                    error_code="ROOM_TYPE_NOT_FOUND",
                    field="room_type_id",
                )
        elif property_.property_room_types and len(property_.property_room_types) == 1:
            room_type_id_db = property_.property_room_types[0].room_type_id

        # 3. Check Availability
        availability = await self.booking_service.check_availability(
            property_id=property_.id,
            room_type_id=room_type_id_db,
            check_in_date=data.check_in_date,
            check_out_date=data.check_out_date,
            num_rooms=data.num_rooms,
        )

        if not availability["is_available"]:
            raise AppException(
                status_code=400,
                message=f"Only {availability['available_units']} room(s) available for the selected dates. Requested {data.num_rooms}.",
                error_code="ROOMS_UNAVAILABLE",
            )

        # 4. Calculate Quote with setting-driven Tax
        tax_rate, is_tax_inclusive, tax_name, tax_code = await self._resolve_tax_settings()
        quote = self.booking_service.calculate_pricing_quote(
            property_=property_,
            check_in_date=data.check_in_date,
            check_out_date=data.check_out_date,
            num_rooms=data.num_rooms,
            num_guests=data.num_guests,
            room_type_id=room_type_id_db,
            tax_rate=tax_rate,
            is_tax_inclusive=is_tax_inclusive,
            tax_name=tax_name,
            tax_code=tax_code,
        )

        # 5. Generate Reference and Create Booking
        booking_reference = self.booking_service.generate_booking_reference()

        booking = Booking(
            booking_reference=booking_reference,
            guest_id=self.current_user.id,
            property_id=property_.id,
            room_type_id=room_type_id_db,
            cancellation_policy_id=property_.cancellation_policy_id,
            check_in_date=data.check_in_date,
            check_out_date=data.check_out_date,
            num_guests=data.num_guests,
            num_rooms=data.num_rooms,
            price_per_night=quote["price_per_night"],
            discount_amount=quote["discount_amount"],
            tax_amount=quote["tax_amount"],
            total_amount=quote["total_amount"],
            currency=quote["currency"],
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            special_requests=data.special_requests,
            created_by=self.current_user.id,
        )

        created_booking = await self.booking_service.create_booking(
            booking=booking,
            with_relations={
                "guest": True,
                "property": True,
                "room_type": True,
                "cancellation_policy": True,
                "payments": True,
                "refund_requests": True,
                "review": True,
            },
        )

        return created_booking
