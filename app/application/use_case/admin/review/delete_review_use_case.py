from app.core.exceptions import AppException
from app.services.review_service import ReviewService


class AdminDeleteReviewUseCase:
    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    async def execute(self, review_id: str) -> None:
        review = await self.review_service.get_by_public_id(review_id)
        if not review:
            raise AppException(404, "Review not found", error_code="REVIEW_NOT_FOUND")

        await self.review_service.delete(review)

