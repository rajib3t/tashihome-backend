from app.application.dto.bookings.booking import AdminBookingQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.repositories.base_repository import Page
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


class AdminGetBookingsUseCase(BaseUseCase):
    def __init__(self, booking_service: BookingService):
        self.booking_service = booking_service

    async def execute(self, params: AdminBookingQueryDTO) -> Page[Booking]:
        return await self.booking_service.list_all_bookings(
            page=params.page,
            page_size=params.size,
            status=params.status,
            payment_status=params.payment_status,
            property_id=int(params.property_id) if params.property_id else None,
            guest_id=int(params.guest_id) if params.guest_id else None,
            check_in_from=params.check_in_from,
            check_in_to=params.check_in_to,
            search=params.search,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            with_relations=_RELATIONS,
        )
