from datetime import datetime, timezone

from app.application.dto.bookings.booking import BookingStatusUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.booking_model import Booking, BookingStatus
from app.services.booking_service import BookingService

# Allowed vendor status transitions: {current_status: [allowed_next_statuses]}
_VENDOR_TRANSITIONS: dict[BookingStatus, list[BookingStatus]] = {
    BookingStatus.PENDING: [BookingStatus.CONFIRMED, BookingStatus.CANCELLED],
    BookingStatus.CONFIRMED: [BookingStatus.CHECKED_IN, BookingStatus.CANCELLED],
    BookingStatus.CHECKED_IN: [BookingStatus.CHECKED_OUT, BookingStatus.NO_SHOW, BookingStatus.CANCELLED],
    BookingStatus.CHECKED_OUT: [],
    BookingStatus.CANCELLED: [],
    BookingStatus.NO_SHOW: [],
    BookingStatus.COMPLETED: [],
}

_RELATIONS = {
    "guest": True,
    "property": True,
    "room_type": True,
    "cancellation_policy": True,
    "payments": True,
    "refund_requests": True,
    "review": True,
}


class VendorUpdateBookingStatusUseCase(BaseUseCase):
    """Vendor can change booking status within permitted transitions."""

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

        # Ownership check — booking must belong to a vendor-owned property
        if booking.property and booking.property.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You do not have access to this booking.",
                error_code="BOOKING_ACCESS_DENIED",
            )

        new_status = BookingStatus(data.status)
        current_status = booking.status
        allowed = _VENDOR_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            raise AppException(
                status_code=400,
                message=(
                    f"Cannot transition booking from '{current_status.value}' to '{new_status.value}'. "
                    f"Allowed transitions: {[s.value for s in allowed] or 'none'}"
                ),
                error_code="INVALID_STATUS_TRANSITION",
            )

        booking.status = new_status
        booking.updated_by = self.current_user.id

        if new_status == BookingStatus.CANCELLED:
            booking.cancellation_reason = data.reason
            booking.cancelled_at = datetime.now(timezone.utc)

        return await self.booking_service.update_booking(
            booking=booking,
            with_relations=_RELATIONS,
        )
