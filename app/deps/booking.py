from fastapi import Depends

from app.application.use_case.user.booking.cancel_booking_use_case import CancelBookingUseCase
from app.application.use_case.user.booking.check_availability_use_case import CheckAvailabilityUseCase
from app.application.use_case.user.booking.create_booking_payment_use_case import (
    CreateBookingPaymentUseCase,
)
from app.application.use_case.user.booking.create_booking_use_case import CreateBookingUseCase
from app.application.use_case.user.booking.get_user_booking_detail_use_case import (
    GetUserBookingDetailUseCase,
)
from app.application.use_case.user.booking.get_user_bookings_use_case import (
    GetUserBookingsUseCase,
)
from app.deps.auth import CurrentUser, get_current_user, require_user
from app.deps.service import (
    get_booking_service,
    get_payment_service,
    get_property_service,
    get_refund_request_service,
    get_room_type_service,
)
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.property_service import PropertyService
from app.services.refund_request_service import RefundRequestService
from app.services.room_type_service import RoomTypeService


async def get_create_booking_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    property_service: PropertyService = Depends(get_property_service),
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CreateBookingUseCase:
    return CreateBookingUseCase(
        booking_service=booking_service,
        property_service=property_service,
        room_type_service=room_type_service,
        current_user=current_user,
    )


async def get_user_bookings_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> GetUserBookingsUseCase:
    return GetUserBookingsUseCase(
        booking_service=booking_service,
        current_user=current_user,
    )


async def get_user_booking_detail_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> GetUserBookingDetailUseCase:
    return GetUserBookingDetailUseCase(
        booking_service=booking_service,
        current_user=current_user,
    )


async def get_cancel_booking_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    refund_request_service: RefundRequestService = Depends(get_refund_request_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CancelBookingUseCase:
    return CancelBookingUseCase(
        booking_service=booking_service,
        refund_request_service=refund_request_service,
        current_user=current_user,
    )


async def get_create_booking_payment_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CreateBookingPaymentUseCase:
    return CreateBookingPaymentUseCase(
        booking_service=booking_service,
        payment_service=payment_service,
        current_user=current_user,
    )


async def get_check_availability_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    property_service: PropertyService = Depends(get_property_service),
    room_type_service: RoomTypeService = Depends(get_room_type_service),
) -> CheckAvailabilityUseCase:
    return CheckAvailabilityUseCase(
        booking_service=booking_service,
        property_service=property_service,
        room_type_service=room_type_service,
    )


from app.application.use_case.user.booking.create_razorpay_order_use_case import (
    CreateRazorpayOrderUseCase,
)
from app.application.use_case.user.booking.verify_razorpay_payment_use_case import (
    VerifyRazorpayPaymentUseCase,
)
from app.deps.service import get_razorpay_service
from app.services.razorpay_service import RazorpayService


async def get_create_razorpay_order_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CreateRazorpayOrderUseCase:
    return CreateRazorpayOrderUseCase(
        booking_service=booking_service,
        razorpay_service=razorpay_service,
        current_user=current_user,
    )


async def get_verify_razorpay_payment_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    payment_service: PaymentService = Depends(get_payment_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> VerifyRazorpayPaymentUseCase:
    return VerifyRazorpayPaymentUseCase(
        booking_service=booking_service,
        payment_service=payment_service,
        razorpay_service=razorpay_service,
        current_user=current_user,
    )

