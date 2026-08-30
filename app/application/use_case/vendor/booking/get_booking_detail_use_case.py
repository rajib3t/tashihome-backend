from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.booking_model import Booking
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


class VendorGetBookingDetailUseCase(BaseUseCase):
    def __init__(self, booking_service: BookingService, current_user: CurrentUser):
        self.booking_service = booking_service
        self.current_user = current_user

    async def execute(self, booking_identifier: str) -> Booking:
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

        # Ensure the booking belongs to one of the vendor's properties
        if booking.property and booking.property.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You do not have access to this booking.",
                error_code="BOOKING_ACCESS_DENIED",
            )

        return booking
