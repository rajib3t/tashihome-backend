from fastapi import Depends

from app.core.events import RedisEventBus

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
from app.deps.auth import CurrentUser, get_current_user, require_admin_or_staff, require_user
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
        event_bus=RedisEventBus(),
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
        event_bus=RedisEventBus(),
    )


# ─────────────────────────────────────────────
# Admin booking dependency factories
# ─────────────────────────────────────────────

from app.application.use_case.admin.bookings.get_bookings_use_case import AdminGetBookingsUseCase
from app.application.use_case.admin.bookings.get_booking_detail_use_case import AdminGetBookingDetailUseCase
from app.application.use_case.admin.bookings.update_booking_status_use_case import AdminUpdateBookingStatusUseCase
from app.deps.auth import require_admin


async def get_admin_bookings_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    _: CurrentUser = Depends(require_admin_or_staff),
) -> AdminGetBookingsUseCase:
    return AdminGetBookingsUseCase(booking_service=booking_service)


async def get_admin_booking_detail_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    _: CurrentUser = Depends(require_admin_or_staff),
) -> AdminGetBookingDetailUseCase:
    return AdminGetBookingDetailUseCase(booking_service=booking_service)


async def get_admin_update_booking_status_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> AdminUpdateBookingStatusUseCase:
    return AdminUpdateBookingStatusUseCase(
        booking_service=booking_service,
        current_user=current_user,
    )


# ─────────────────────────────────────────────
# Vendor booking dependency factories
# ─────────────────────────────────────────────

from app.application.use_case.vendor.booking.get_bookings_use_case import VendorGetBookingsUseCase
from app.application.use_case.vendor.booking.get_booking_detail_use_case import VendorGetBookingDetailUseCase
from app.application.use_case.vendor.booking.update_booking_status_use_case import VendorUpdateBookingStatusUseCase
from app.deps.auth import require_vendor


async def get_vendor_bookings_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorGetBookingsUseCase:
    return VendorGetBookingsUseCase(
        booking_service=booking_service,
        current_user=current_user,
    )


async def get_vendor_booking_detail_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorGetBookingDetailUseCase:
    return VendorGetBookingDetailUseCase(
        booking_service=booking_service,
        current_user=current_user,
    )


async def get_vendor_update_booking_status_use_case(
    booking_service: BookingService = Depends(get_booking_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorUpdateBookingStatusUseCase:
    return VendorUpdateBookingStatusUseCase(
        booking_service=booking_service,
        current_user=current_user,
    )


# ─────────────────────────────────────────────
# Admin refund dependency factories
# ─────────────────────────────────────────────

from app.application.use_case.admin.bookings.list_refund_requests_use_case import AdminListRefundRequestsUseCase
from app.application.use_case.admin.bookings.get_refund_request_use_case import AdminGetRefundRequestUseCase
from app.application.use_case.admin.bookings.update_refund_request_use_case import (
    AdminUpdateRefundStatusUseCase,
    AdminProcessRefundUseCase,
)
from app.deps.service import get_payment_service, get_razorpay_service
from app.services.payment_service import PaymentService
from app.services.razorpay_service import RazorpayService


async def get_admin_list_refund_requests_use_case(
    refund_request_service: RefundRequestService = Depends(get_refund_request_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminListRefundRequestsUseCase:
    return AdminListRefundRequestsUseCase(refund_request_service=refund_request_service)


async def get_admin_get_refund_request_use_case(
    refund_request_service: RefundRequestService = Depends(get_refund_request_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminGetRefundRequestUseCase:
    return AdminGetRefundRequestUseCase(refund_request_service=refund_request_service)


async def get_admin_update_refund_status_use_case(
    refund_request_service: RefundRequestService = Depends(get_refund_request_service),
    current_user: CurrentUser = Depends(require_admin),
) -> AdminUpdateRefundStatusUseCase:
    return AdminUpdateRefundStatusUseCase(
        refund_request_service=refund_request_service,
        current_user=current_user,
    )


async def get_admin_process_refund_use_case(
    refund_request_service: RefundRequestService = Depends(get_refund_request_service),
    payment_service: PaymentService = Depends(get_payment_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    current_user: CurrentUser = Depends(require_admin),
) -> AdminProcessRefundUseCase:
    return AdminProcessRefundUseCase(
        refund_request_service=refund_request_service,
        payment_service=payment_service,
        razorpay_service=razorpay_service,
        current_user=current_user,
    )
