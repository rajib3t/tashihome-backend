from app.application.dto.review import ReviewStatusUpdateDTO
from app.core.exceptions import AppException
from app.models.review_model import Review, ReviewStatus
from app.services.review_service import ReviewService


class AdminUpdateReviewStatusUseCase:
    def __init__(self, review_service: ReviewService):
        self.review_service = review_service

    async def execute(self, review_id: str, dto: ReviewStatusUpdateDTO) -> Review:
        review = await self.review_service.get_by_public_id(
            review_id,
            with_relations={"booking": True, "guest": True, "property": True},
        )
        if not review:
            raise AppException(404, "Review not found", error_code="REVIEW_NOT_FOUND")

        try:
            review.status = ReviewStatus(dto.status.lower())
        except ValueError:
            try:
                review.status = ReviewStatus[dto.status.upper()]
            except KeyError:
                raise AppException(400, f"Invalid status '{dto.status}'", error_code="INVALID_STATUS")

        return await self.review_service.update(
            review,
            with_relations={"booking": True, "guest": True, "property": True},
        )

