from typing import Optional

from app.application.dto.review import ReviewQueryDTO
from app.models.review_model import Review
from app.repositories.base_repository import Page
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService


class AdminListReviewsUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        property_service: Optional[PropertyService] = None,
    ):
        self.review_service = review_service
        self.property_service = property_service

    async def execute(self, params: ReviewQueryDTO) -> Page[Review]:
        property_internal_id = None
        if params.property_id and self.property_service:
            prop = await self.property_service.get_by_public_id(params.property_id)
            if prop:
                property_internal_id = prop.id

        return await self.review_service.list_all(
            page=params.page,
            page_size=params.page_size,
            status=params.status,
            property_id=property_internal_id,
            search=params.search,
            sort_order=params.sort_order,
            with_relations={"booking": True, "guest": True, "property": True},
        )

