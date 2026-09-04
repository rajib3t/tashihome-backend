from typing import Any, Dict, Tuple

from app.application.dto.review import ReviewQueryDTO
from app.core.exceptions import AppException
from app.models.review_model import Review
from app.repositories.base_repository import Page
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService


class GetPublicPropertyReviewsUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        property_service: PropertyService,
    ):
        self.review_service = review_service
        self.property_service = property_service

    async def execute(self, property_id: str, params: ReviewQueryDTO) -> Tuple[Page[Review], Dict[str, Any]]:
        # 1. Resolve property by public_id or slug
        property_obj = await self.property_service.get_property_by_public_id(property_id)
        if not property_obj:
            property_obj = await self.property_service.get_property_by_slug(property_id)

        if not property_obj:
            raise AppException(404, "Property not found", error_code="PROPERTY_NOT_FOUND")

        # 2. Get paginated published reviews
        reviews_page = await self.review_service.list_by_property(
            property_id=property_obj.id,
            status="published",
            page=params.page,
            page_size=params.page_size,
            sort_order=params.sort_order,
            with_relations={"booking": True, "guest": True, "property": True},
        )

        # 3. Get rating summary
        rating_summary = await self.review_service.get_property_rating_summary(property_obj.id)

        return reviews_page, rating_summary

