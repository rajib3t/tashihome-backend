from app.application.dto.review import ReviewUpdateDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.review_model import Review, ReviewStatus
from app.services.review_service import ReviewService


class UpdateReviewUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        current_user: CurrentUser,
    ):
        self.review_service = review_service
        self.current_user = current_user

    async def execute(self, review_id: str, dto: ReviewUpdateDTO) -> Review:
        review = await self.review_service.get_by_public_id(
            review_id,
            with_relations={"booking": True, "guest": True, "property": True},
        )
        if not review:
            raise AppException(404, "Review not found", error_code="REVIEW_NOT_FOUND")

        if review.guest_id != self.current_user.id:
            raise AppException(403, "You can only update your own reviews", error_code="FORBIDDEN")

        if dto.rating is not None:
            review.rating = dto.rating
        if dto.comment is not None:
            review.comment = dto.comment

        # Editing resets status to PENDING for admin review
        review.status = ReviewStatus.PENDING

        return await self.review_service.update(
            review,
            with_relations={"booking": True, "guest": True, "property": True},
        )

