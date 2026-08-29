from datetime import date
from typing import Any, Dict, Optional
from uuid import UUID

from app.application.dto.bookings.booking import BookingAvailabilityDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.property_model import PropertyStatus
from app.services.booking_service import BookingService
from app.services.property_service import PropertyService
from app.services.room_type_service import RoomTypeService


class CheckAvailabilityUseCase(BaseUseCase):
    def __init__(
        self,
        booking_service: BookingService,
        property_service: PropertyService,
        room_type_service: RoomTypeService,
    ):
        self.booking_service = booking_service
        self.property_service = property_service
        self.room_type_service = room_type_service

    async def execute(self, data: BookingAvailabilityDTO) -> Dict[str, Any]:
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
                with_relations={"property_room_types": True},
            )
        except (ValueError, AttributeError):
            if str(data.property_id).isdigit():
                property_ = await self.property_service.get_by_id(
                    int(data.property_id),
                    with_relations={"property_room_types": True},
                )
            else:
                property_ = await self.property_service.get_by_slug(
                    str(data.property_id),
                    with_relations={"property_room_types": True},
                )

        if not property_:
            raise AppException(
                status_code=404,
                message="Property not found.",
                error_code="PROPERTY_NOT_FOUND",
                field="property_id",
            )

        # 2. Resolve Room Type if provided
        room_type_id_db: Optional[int] = None
        if data.room_type_id:
            room_type = None
            try:
                rt_uuid = UUID(str(data.room_type_id))
                room_type = await self.room_type_service.get_by_public_id(str(rt_uuid))
            except (ValueError, AttributeError):
                if str(data.room_type_id).isdigit():
                    room_type = await self.room_type_service.get_by_id(int(data.room_type_id))

            if not room_type:
                raise AppException(
                    status_code=404,
                    message="Room type not found.",
                    error_code="ROOM_TYPE_NOT_FOUND",
                    field="room_type_id",
                )
            room_type_id_db = room_type.id

        # 3. Check Availability
        availability = await self.booking_service.check_availability(
            property_id=property_.id,
            room_type_id=room_type_id_db,
            check_in_date=data.check_in_date,
            check_out_date=data.check_out_date,
            num_rooms=data.num_rooms,
        )

        quote = None
        if availability["is_available"]:
            quote = self.booking_service.calculate_pricing_quote(
                property_=property_,
                check_in_date=data.check_in_date,
                check_out_date=data.check_out_date,
                num_rooms=data.num_rooms,
                num_guests=data.num_guests,
            )

        return {
            "is_available": availability["is_available"],
            "available_units": availability["available_units"],
            "total_units": availability["total_units"],
            "booked_units": availability["booked_units"],
            "blocked_units": availability["blocked_units"],
            "requested_rooms": data.num_rooms,
            "quote": quote,
        }

