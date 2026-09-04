from fastapi import APIRouter, Body, Depends

from app.api.base_controller import BaseController
from app.application.dto.review import (
    ReviewHostReplyDTO,
    ReviewQueryDTO,
)
from app.application.use_case.vendor.review.list_vendor_reviews_use_case import ListVendorReviewsUseCase
from app.application.use_case.vendor.review.reply_review_use_case import VendorReplyReviewUseCase
from app.core.csrf import verify_csrf
from app.deps.review import (
    get_vendor_list_reviews_use_case,
    get_vendor_reply_review_use_case,
)
from app.schemas.review_schema import (
    ReviewListResponseSchema,
    ReviewResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class VendorReviewController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/reviews",
            tags=["Vendor - Reviews"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/",
                self._get_reviews,
                {"response_model": ReviewListResponseSchema},
            ),
            (
                "post",
                "/{review_id}/reply",
                self._reply_review,
                {
                    "response_model": ReviewResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_reviews(
        self,
        params: ReviewQueryDTO = Depends(),
        use_case: ListVendorReviewsUseCase = Depends(get_vendor_list_reviews_use_case),
    ):
        result = await use_case.execute(params)
        return self.build_response(
            message="Property reviews retrieved successfully.",
            data=result.items,
            meta=self.pagination_meta(result),
        )

    @handle_api_exceptions
    async def _reply_review(
        self,
        review_id: str,
        data: ReviewHostReplyDTO = Body(...),
        use_case: VendorReplyReviewUseCase = Depends(get_vendor_reply_review_use_case),
    ):
        result = await use_case.execute(review_id, data)
        return self.build_response(
            message="Host reply submitted successfully.",
            data=result,
        )


controller = VendorReviewController()
router = controller.router

