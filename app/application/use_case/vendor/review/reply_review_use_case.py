from datetime import datetime, timezone

from app.application.dto.review import ReviewHostReplyDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.review_model import Review
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService


class VendorReplyReviewUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        property_service: PropertyService,
        current_user: CurrentUser,
    ):
        self.review_service = review_service
        self.property_service = property_service
        self.current_user = current_user

    async def execute(self, review_id: str, dto: ReviewHostReplyDTO) -> Review:
        review = await self.review_service.get_by_public_id(
            review_id,
            with_relations={"booking": True, "guest": True, "property": True},
        )
        if not review:
            raise AppException(404, "Review not found", error_code="REVIEW_NOT_FOUND")

        # Verify that property belongs to current vendor
        property_obj = await self.property_service.get_property_by_id(review.property_id)
        if not property_obj or property_obj.vendor_id != self.current_user.id:
            raise AppException(403, "You can only reply to reviews for your own properties", error_code="FORBIDDEN")

        review.host_reply = dto.host_reply
        review.host_replied_at = datetime.now(timezone.utc)

        return await self.review_service.update(
            review,
            with_relations={"booking": True, "guest": True, "property": True},
        )

