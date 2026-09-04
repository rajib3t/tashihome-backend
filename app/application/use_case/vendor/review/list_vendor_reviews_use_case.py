from datetime import datetime, timezone
from typing import Optional

from app.application.dto.review import ReviewQueryDTO
from app.deps.auth import CurrentUser
from app.models.review_model import Review
from app.repositories.base_repository import Page
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService


class ListVendorReviewsUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        property_service: PropertyService,
        current_user: CurrentUser,
    ):
        self.review_service = review_service
        self.property_service = property_service
        self.current_user = current_user

    async def execute(self, params: ReviewQueryDTO) -> Page[Review]:
        # 1. Fetch vendor's properties
        vendor_properties = await self.property_service.get_properties_by_vendor(
            self.current_user.id
        )
        property_ids = [p.id for p in vendor_properties]

        if not property_ids:
            return Page(items=[], total=0, page=params.page, page_size=params.page_size)

        return await self.review_service.list_by_vendor_properties(
            property_ids=property_ids,
            status=params.status,
            page=params.page,
            page_size=params.page_size,
            sort_order=params.sort_order,
            with_relations={"booking": True, "guest": True, "property": True},
        )

