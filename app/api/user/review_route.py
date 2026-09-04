from fastapi import APIRouter, Body, Depends

from app.api.base_controller import BaseController
from app.application.dto.review import (
    ReviewCreateDTO,
    ReviewQueryDTO,
    ReviewUpdateDTO,
)
from app.application.use_case.user.review.create_review_use_case import CreateReviewUseCase
from app.application.use_case.user.review.delete_review_use_case import DeleteReviewUseCase
from app.application.use_case.user.review.get_review_detail_use_case import GetReviewDetailUseCase
from app.application.use_case.user.review.get_user_reviews_use_case import GetUserReviewsUseCase
from app.application.use_case.user.review.update_review_use_case import UpdateReviewUseCase
from app.core.csrf import verify_csrf
from app.deps.idempotency import require_idempotency_key
from app.deps.review import (
    get_create_review_use_case,
    get_delete_review_use_case,
    get_review_detail_use_case,
    get_update_review_use_case,
    get_user_reviews_use_case,
)
from app.schemas.review_schema import (
    ReviewListResponseSchema,
    ReviewResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class UserReviewController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/reviews",
            tags=["User - Reviews"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "post",
                "/",
                self._create_review,
                {
                    "response_model": ReviewResponseSchema,
                    "status_code": 201,
                    "dependencies": [Depends(verify_csrf), Depends(require_idempotency_key)],
                },
            ),
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
                "put",
                "/{review_id}",
                self._update_review,
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
    async def _create_review(
        self,
        data: ReviewCreateDTO,
        use_case: CreateReviewUseCase = Depends(get_create_review_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Review submitted successfully and is pending approval.",
            data=result,
        )

    @handle_api_exceptions
    async def _get_reviews(
        self,
        params: ReviewQueryDTO = Depends(),
        use_case: GetUserReviewsUseCase = Depends(get_user_reviews_use_case),
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
        use_case: GetReviewDetailUseCase = Depends(get_review_detail_use_case),
    ):
        result = await use_case.execute(review_id)
        return self.build_response(
            message="Review retrieved successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _update_review(
        self,
        review_id: str,
        data: ReviewUpdateDTO = Body(...),
        use_case: UpdateReviewUseCase = Depends(get_update_review_use_case),
    ):
        result = await use_case.execute(review_id, data)
        return self.build_response(
            message="Review updated successfully and is pending approval.",
            data=result,
        )

    @handle_api_exceptions
    async def _delete_review(
        self,
        review_id: str,
        use_case: DeleteReviewUseCase = Depends(get_delete_review_use_case),
    ):
        await use_case.execute(review_id)
        return self.build_response(
            message="Review deleted successfully.",
            data=None,
        )


controller = UserReviewController()
router = controller.router

