from fastapi import APIRouter, Body, Depends

from app.api.base_controller import BaseController
from app.application.dto.bookings.booking import (
    BookingAvailabilityDTO,
    BookingCancelDTO,
    BookingCreateDTO,
    BookingPaymentDTO,
    BookingQueryDTO,
    RazorpayCreateOrderDTO,
    RazorpayVerifyPaymentDTO,
)
from app.application.use_case.user.booking.cancel_booking_use_case import CancelBookingUseCase
from app.application.use_case.user.booking.check_availability_use_case import (
    CheckAvailabilityUseCase,
)
from app.application.use_case.user.booking.create_booking_payment_use_case import (
    CreateBookingPaymentUseCase,
)
from app.application.use_case.user.booking.create_booking_use_case import CreateBookingUseCase
from app.application.use_case.user.booking.create_razorpay_order_use_case import (
    CreateRazorpayOrderUseCase,
)
from app.application.use_case.user.booking.get_user_booking_detail_use_case import (
    GetUserBookingDetailUseCase,
)
from app.application.use_case.user.booking.get_user_bookings_use_case import (
    GetUserBookingsUseCase,
)
from app.application.use_case.user.booking.verify_razorpay_payment_use_case import (
    VerifyRazorpayPaymentUseCase,
)
from app.core.csrf import verify_csrf
from app.deps.idempotency import require_idempotency_key
from app.deps.booking import (
    get_cancel_booking_use_case,
    get_check_availability_use_case,
    get_create_booking_payment_use_case,
    get_create_booking_use_case,
    get_create_razorpay_order_use_case,
    get_user_booking_detail_use_case,
    get_user_bookings_use_case,
    get_verify_razorpay_payment_use_case,
)
from app.deps.service import get_payment_service
from app.schemas.booking_schema import (
    BookingAvailabilityResponseSchema,
    BookingCancelResponseSchema,
    BookingListResponseSchema,
    BookingPaymentListResponseSchema,
    BookingPaymentResponseSchema,
    BookingResponseSchema,
    RazorpayOrderResponseSchema,
)
from app.services.payment_service import PaymentService
from app.utils.exception_decorate import handle_api_exceptions


class UserBookingController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/bookings",
            tags=["User - Bookings"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "post",
                "/",
                self._create_booking,
                {
                    "response_model": BookingResponseSchema,
                    "status_code": 201,
                    "dependencies": [Depends(verify_csrf), Depends(require_idempotency_key)],
                },
            ),
            (
                "get",
                "/",
                self._get_bookings,
                {"response_model": BookingListResponseSchema},
            ),
            (
                "post",
                "/check-availability",
                self._check_availability,
                {"response_model": BookingAvailabilityResponseSchema},
            ),
            (
                "get",
                "/{booking_id}",
                self._get_booking,
                {"response_model": BookingResponseSchema},
            ),
            (
                "post",
                "/{booking_id}/cancel",
                self._cancel_booking,
                {
                    "response_model": BookingCancelResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "post",
                "/{booking_id}/payments",
                self._create_payment,
                {
                    "response_model": BookingPaymentResponseSchema,
                    "status_code": 201,
                    "dependencies": [Depends(verify_csrf), Depends(require_idempotency_key)],
                },
            ),
            (
                "get",
                "/{booking_id}/payments",
                self._get_payments,
                {"response_model": BookingPaymentListResponseSchema},
            ),
            (
                "post",
                "/{booking_id}/razorpay/order",
                self._create_razorpay_order,
                {
                    "response_model": RazorpayOrderResponseSchema,
                    "status_code": 201,
                    "dependencies": [Depends(verify_csrf), Depends(require_idempotency_key)],
                },
            ),
            (
                "post",
                "/{booking_id}/razorpay/verify",
                self._verify_razorpay_payment,
                {
                    "response_model": BookingPaymentResponseSchema,
                    "dependencies": [Depends(verify_csrf), Depends(require_idempotency_key)],
                },
            ),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _create_booking(
        self,
        data: BookingCreateDTO,
        use_case: CreateBookingUseCase = Depends(get_create_booking_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Booking created successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _get_bookings(
        self,
        params: BookingQueryDTO = Depends(),
        use_case: GetUserBookingsUseCase = Depends(get_user_bookings_use_case),
    ):
        result = await use_case.execute(params)
        return self.build_response(
            message="Bookings retrieved successfully.",
            data=result.items,
            meta=self.pagination_meta(result),
        )

    @handle_api_exceptions
    async def _check_availability(
        self,
        data: BookingAvailabilityDTO,
        use_case: CheckAvailabilityUseCase = Depends(get_check_availability_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Availability check completed.",
            data=result,
        )

    @handle_api_exceptions
    async def _get_booking(
        self,
        booking_id: str,
        use_case: GetUserBookingDetailUseCase = Depends(get_user_booking_detail_use_case),
    ):
        result = await use_case.execute(booking_id)
        return self.build_response(
            message="Booking retrieved successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _cancel_booking(
        self,
        booking_id: str,
        data: BookingCancelDTO = Body(default=BookingCancelDTO()),
        use_case: CancelBookingUseCase = Depends(get_cancel_booking_use_case),
    ):
        result = await use_case.execute(booking_id, data)
        return self.build_response(
            message="Booking cancelled successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _create_payment(
        self,
        booking_id: str,
        data: BookingPaymentDTO = Body(...),
        use_case: CreateBookingPaymentUseCase = Depends(get_create_booking_payment_use_case),
    ):
        result = await use_case.execute(booking_id, data)
        return self.build_response(
            message="Payment recorded successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _get_payments(
        self,
        booking_id: str,
        booking_use_case: GetUserBookingDetailUseCase = Depends(get_user_booking_detail_use_case),
        payment_service: PaymentService = Depends(get_payment_service),
    ):
        booking = await booking_use_case.execute(booking_id)
        payments = await payment_service.list_by_booking_id(booking.id)
        return self.build_response(
            message="Payments retrieved successfully.",
            data=payments,
        )

    @handle_api_exceptions
    async def _create_razorpay_order(
        self,
        booking_id: str,
        data: RazorpayCreateOrderDTO = Body(default=RazorpayCreateOrderDTO()),
        use_case: CreateRazorpayOrderUseCase = Depends(get_create_razorpay_order_use_case),
    ):
        result = await use_case.execute(booking_id, data)
        return self.build_response(
            message="Razorpay order created successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _verify_razorpay_payment(
        self,
        booking_id: str,
        data: RazorpayVerifyPaymentDTO = Body(...),
        use_case: VerifyRazorpayPaymentUseCase = Depends(get_verify_razorpay_payment_use_case),
    ):
        result = await use_case.execute(booking_id, data)
        return self.build_response(
            message="Razorpay payment verified successfully.",
            data=result,
        )


controller = UserBookingController()
router = controller.router

