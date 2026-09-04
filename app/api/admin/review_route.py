from fastapi import APIRouter, Body, Depends

from app.api.base_controller import BaseController
from app.application.dto.review import ReviewQueryDTO, ReviewStatusUpdateDTO
from app.application.use_case.admin.review.approve_review_use_case import AdminApproveReviewUseCase
from app.application.use_case.admin.review.delete_review_use_case import AdminDeleteReviewUseCase
from app.application.use_case.admin.review.get_review_use_case import AdminGetReviewUseCase
from app.application.use_case.admin.review.list_reviews_use_case import AdminListReviewsUseCase
from app.application.use_case.admin.review.reject_review_use_case import AdminRejectReviewUseCase
from app.application.use_case.admin.review.update_review_status_use_case import AdminUpdateReviewStatusUseCase
from app.core.csrf import verify_csrf
from app.deps.review import (
    get_admin_approve_review_use_case,
    get_admin_delete_review_use_case,
    get_admin_get_review_use_case,
    get_admin_list_reviews_use_case,
    get_admin_reject_review_use_case,
    get_admin_update_review_status_use_case,
)
from app.schemas.review_schema import ReviewListResponseSchema, ReviewResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class AdminReviewController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/reviews",
            tags=["Admin - Reviews"],
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
                "get",
                "/{review_id}",
                self._get_review,
                {"response_model": ReviewResponseSchema},
            ),
            (
                "post",
                "/{review_id}/approve",
                self._approve_review,
                {
                    "response_model": ReviewResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "post",
                "/{review_id}/reject",
                self._reject_review,
                {
                    "response_model": ReviewResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "patch",
                "/{review_id}/status",
                self._update_status,
                {
                    "response_model": ReviewResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "delete",
                "/{review_id}",
                self._delete_review,
                {
                    "status_code": 200,
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
        use_case: AdminListReviewsUseCase = Depends(get_admin_list_reviews_use_case),
    ):
        result = await use_case.execute(params)
        return self.build_response(
            message="Reviews retrieved successfully.",
            data=result.items,
            meta=self.pagination_meta(result),
        )

    @handle_api_exceptions
    async def _get_review(
        self,
        review_id: str,
        use_case: AdminGetReviewUseCase = Depends(get_admin_get_review_use_case),
    ):
        result = await use_case.execute(review_id)
        return self.build_response(
            message="Review retrieved successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _approve_review(
        self,
        review_id: str,
        use_case: AdminApproveReviewUseCase = Depends(get_admin_approve_review_use_case),
    ):
        result = await use_case.execute(review_id)
        return self.build_response(
            message="Review approved successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _reject_review(
        self,
        review_id: str,
        use_case: AdminRejectReviewUseCase = Depends(get_admin_reject_review_use_case),
    ):
        result = await use_case.execute(review_id)
        return self.build_response(
            message="Review rejected successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _update_status(
        self,
        review_id: str,
        data: ReviewStatusUpdateDTO = Body(...),
        use_case: AdminUpdateReviewStatusUseCase = Depends(get_admin_update_review_status_use_case),
    ):
        result = await use_case.execute(review_id, data)
        return self.build_response(
            message="Review status updated successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _delete_review(
        self,
        review_id: str,
        use_case: AdminDeleteReviewUseCase = Depends(get_admin_delete_review_use_case),
    ):
        await use_case.execute(review_id)
        return self.build_response(
            message="Review deleted successfully.",
            data=None,
        )


controller = AdminReviewController()
router = controller.router

