from datetime import datetime, timezone

from app.application.dto.bookings.booking import BookingStatusUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.booking_model import Booking, BookingStatus
from app.services.booking_service import BookingService

_RELATIONS = {
    "guest": True,
    "property": True,
    "room_type": True,
    "cancellation_policy": True,
    "payments": True,
    "refund_requests": True,
    "review": True,
}


class AdminUpdateBookingStatusUseCase(BaseUseCase):
    """Admin can change a booking to any status."""

    def __init__(self, booking_service: BookingService, current_user: CurrentUser):
        self.booking_service = booking_service
        self.current_user = current_user

    async def execute(self, booking_identifier: str, data: BookingStatusUpdateDTO) -> Booking:
        booking = await self.booking_service.get_booking_by_identifier(
            identifier=booking_identifier,
            with_relations=_RELATIONS,
        )
        if not booking:
            raise AppException(
                status_code=404,
                message="Booking not found.",
                error_code="BOOKING_NOT_FOUND",
                field="booking_id",
            )

        new_status = BookingStatus(data.status)
        booking.status = new_status
        booking.updated_by = self.current_user.id

        if new_status == BookingStatus.CANCELLED:
            booking.cancellation_reason = data.reason
            booking.cancelled_at = datetime.now(timezone.utc)

        return await self.booking_service.update_booking(
            booking=booking,
            with_relations=_RELATIONS,
        )
