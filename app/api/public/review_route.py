from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.review import ReviewQueryDTO
from app.application.use_case.public.review.get_property_reviews_use_case import (
    GetPublicPropertyReviewsUseCase,
)
from app.deps.review import get_public_property_reviews_use_case
from app.schemas.review_schema import (
    PropertyRatingSummaryResponseSchema,
    ReviewListResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class PublicReviewController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/reviews",
            tags=["Public - Reviews"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/property/{property_id}",
                self._get_property_reviews,
                {"response_model": ReviewListResponseSchema},
            ),
            (
                "get",
                "/property/{property_id}/summary",
                self._get_property_rating_summary,
                {"response_model": PropertyRatingSummaryResponseSchema},
            ),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_property_reviews(
        self,
        property_id: str,
        params: ReviewQueryDTO = Depends(),
        use_case: GetPublicPropertyReviewsUseCase = Depends(get_public_property_reviews_use_case),
    ):
        reviews_page, rating_summary = await use_case.execute(property_id, params)
        meta = self.pagination_meta(reviews_page)
        meta["summary"] = rating_summary
        return self.build_response(
            message="Property reviews retrieved successfully.",
            data=reviews_page.items,
            meta=meta,
        )

    @handle_api_exceptions
    async def _get_property_rating_summary(
        self,
        property_id: str,
        use_case: GetPublicPropertyReviewsUseCase = Depends(get_public_property_reviews_use_case),
    ):
        _, rating_summary = await use_case.execute(property_id, ReviewQueryDTO(page=1, page_size=1))
        return self.build_response(
            message="Property rating summary retrieved successfully.",
            data=rating_summary,
        )


controller = PublicReviewController()
router = controller.router

