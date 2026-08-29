from app.application.dto.bookings.booking import BookingQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.models.booking_model import Booking
from app.repositories.base_repository import Page
from app.services.booking_service import BookingService


class GetUserBookingsUseCase(BaseUseCase):
    def __init__(
        self,
        booking_service: BookingService,
        current_user: CurrentUser,
    ):
        self.booking_service = booking_service
        self.current_user = current_user

    async def execute(self, params: BookingQueryDTO) -> Page[Booking]:
        return await self.booking_service.list_user_bookings(
            guest_id=self.current_user.id,
            page=params.page,
            page_size=params.size,
            status=params.status,
            payment_status=params.payment_status,
            search=params.search,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
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

