from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.bookings.booking import AdminBookingQueryDTO, BookingStatusUpdateDTO
from app.application.use_case.admin.bookings.get_bookings_use_case import AdminGetBookingsUseCase
from app.application.use_case.admin.bookings.get_booking_detail_use_case import AdminGetBookingDetailUseCase
from app.application.use_case.admin.bookings.update_booking_status_use_case import AdminUpdateBookingStatusUseCase
from app.deps.booking import (
    get_admin_bookings_use_case,
    get_admin_booking_detail_use_case,
    get_admin_update_booking_status_use_case,
)
from app.schemas.booking_schema import BookingListResponseSchema, BookingResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class BookingController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/bookings",
            tags=["Admin - Bookings"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_bookings, {"response_model": BookingListResponseSchema}),
            ("get", "/{booking_id}", self._get_booking, {"response_model": BookingResponseSchema}),
            ("patch", "/{booking_id}/status", self._update_booking_status, {"response_model": BookingResponseSchema}),
        ]
        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)

    @handle_api_exceptions
    async def _get_bookings(
        self,
        params: AdminBookingQueryDTO = Depends(),
        use_case: AdminGetBookingsUseCase = Depends(get_admin_bookings_use_case),
    ):
        page = await use_case.execute(params)
        return self.build_response(
            message="Bookings retrieved successfully.",
            data=page.items,
            meta=self.pagination_meta(page),
        )

    @handle_api_exceptions
    async def _get_booking(
        self,
        booking_id: str,
        use_case: AdminGetBookingDetailUseCase = Depends(get_admin_booking_detail_use_case),
    ):
        booking = await use_case.execute(booking_id)
        return self.build_response(
            message="Booking retrieved successfully.",
            data=booking,
        )

    @handle_api_exceptions
    async def _update_booking_status(
        self,
        booking_id: str,
        data: BookingStatusUpdateDTO,
        use_case: AdminUpdateBookingStatusUseCase = Depends(get_admin_update_booking_status_use_case),
    ):
        booking = await use_case.execute(booking_id, data)
        return self.build_response(
            message="Booking status updated successfully.",
            data=booking,
        )


controller = BookingController()
router = controller.router
