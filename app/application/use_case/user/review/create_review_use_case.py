from app.application.dto.review import ReviewCreateDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.booking_model import BookingStatus
from app.models.review_model import Review, ReviewStatus
from app.services.booking_service import BookingService
from app.services.review_service import ReviewService


class CreateReviewUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        booking_service: BookingService,
        current_user: CurrentUser,
    ):
        self.review_service = review_service
        self.booking_service = booking_service
        self.current_user = current_user

    async def execute(self, dto: ReviewCreateDTO) -> Review:
        # 1. Resolve booking identifier (accepts UUID public_id or booking_reference string)
        identifier = dto.booking_id or dto.booking_reference
        if not identifier:
            raise AppException(
                400,
                "Please provide a valid booking_id or booking_reference",
                error_code="INVALID_BOOKING_IDENTIFIER",
                field="booking_id",
            )

        booking = await self.booking_service.get_booking_by_identifier(identifier)
        if not booking:
            raise AppException(404, "Booking not found", error_code="BOOKING_NOT_FOUND")

        # 2. Check ownership
        if booking.guest_id != self.current_user.id:
            raise AppException(403, "You can only review your own bookings", error_code="FORBIDDEN")

        # 3. Check booking status (allow COMPLETED, CHECKED_OUT, or CONFIRMED)
        allowed_statuses = [
            BookingStatus.COMPLETED,
            BookingStatus.CHECKED_OUT,
            BookingStatus.CONFIRMED,
        ]
        if booking.status not in allowed_statuses:
            raise AppException(
                400,
                f"Cannot review booking with status '{booking.status.value}'",
                error_code="INVALID_BOOKING_STATUS",
            )

        # 4. Check if review already exists for this booking
        existing = await self.review_service.get_by_booking_id(booking.id)
        if existing:
            raise AppException(
                409,
                "A review has already been submitted for this booking",
                error_code="REVIEW_ALREADY_EXISTS",
            )

        # 5. Create new review with status PENDING for admin approval
        review = Review(
            booking_id=booking.id,
            guest_id=self.current_user.id,
            property_id=booking.property_id,
            rating=dto.rating,
            comment=dto.comment,
            status=ReviewStatus.PENDING,
        )

        return await self.review_service.create(
            review,
            with_relations={"booking": True, "guest": True, "property": True},
        )

