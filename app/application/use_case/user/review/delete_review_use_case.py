from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.services.review_service import ReviewService


class DeleteReviewUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        current_user: CurrentUser,
    ):
        self.review_service = review_service
        self.current_user = current_user

    async def execute(self, review_id: str) -> None:
        review = await self.review_service.get_by_public_id(review_id)
        if not review:
            raise AppException(404, "Review not found", error_code="REVIEW_NOT_FOUND")

        if review.guest_id != self.current_user.id and self.current_user.role not in ["admin", "staff"]:
            raise AppException(403, "You can only delete your own reviews", error_code="FORBIDDEN")

        await self.review_service.delete(review)

