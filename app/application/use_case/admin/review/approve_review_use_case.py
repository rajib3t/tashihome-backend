from app.core.exceptions import AppException
from app.models.review_model import Review, ReviewStatus
from app.services.review_service import ReviewService


class AdminApproveReviewUseCase:
    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    async def execute(self, review_id: str) -> Review:
        review = await self.review_service.get_by_public_id(
            review_id,
            with_relations={"booking": True, "guest": True, "property": True},
        )
        if not review:
            raise AppException(404, "Review not found", error_code="REVIEW_NOT_FOUND")

        review.status = ReviewStatus.PUBLISHED

        return await self.review_service.update(
            review,
            with_relations={"booking": True, "guest": True, "property": True},
        )

