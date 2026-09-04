from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.review_model import Review
from app.services.review_service import ReviewService


class GetReviewDetailUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        current_user: CurrentUser,
    ):
        self.review_service = review_service
        self.current_user = current_user

    async def execute(self, review_id: str) -> Review:
        review = await self.review_service.get_by_public_id(
            review_id,
            with_relations={"booking": True, "guest": True, "property": True},
        )
        if not review:
            raise AppException(404, "Review not found", error_code="REVIEW_NOT_FOUND")

        if review.guest_id != self.current_user.id and self.current_user.role not in ["admin", "staff"]:
            raise AppException(403, "Access denied", error_code="FORBIDDEN")

        return review

