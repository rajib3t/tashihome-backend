from app.application.dto.review import ReviewQueryDTO
from app.deps.auth import CurrentUser
from app.models.review_model import Review
from app.repositories.base_repository import Page
from app.services.review_service import ReviewService


class GetUserReviewsUseCase:
    def __init__(
        self,
        review_service: ReviewService,
        current_user: CurrentUser,
    ):
        self.review_service = review_service
        self.current_user = current_user

    async def execute(self, params: ReviewQueryDTO) -> Page[Review]:
        return await self.review_service.list_by_guest(
            guest_id=self.current_user.id,
            page=params.page,
            page_size=params.page_size,
            sort_order=params.sort_order,
            with_relations={"booking": True, "guest": True, "property": True},
        )

